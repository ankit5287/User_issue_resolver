import os
import datetime
from collections import Counter
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from .models import Issue
from .forms import IssueForm
from .algorithms.sentiment import analyze_sentiment, get_sentiment_category, get_sentiment_analytics
from .algorithms.urgency import calculate_urgency
from .algorithms.team_classifier import classify_team
from .algorithms.priority_queue import push_issue, pop_issue, get_top_n
from .algorithms.search_index import add_to_index, search_index
from .queue_manager import issue_priority_queue
from .search_manager import issue_search_index
from django.db.models import Count


# Configure Matplotlib non-interactive Agg backend safely (with fallback for serverless environments)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

def apply_dark_theme():
    """Configure matplotlib rcParams to use high-contrast dark theme matching dashboard style."""
    if not HAS_MATPLOTLIB or plt is None:
        return
    try:
        plt.rcParams['figure.facecolor'] = '#1E2128'
        plt.rcParams['axes.facecolor'] = '#1E2128'
        plt.rcParams['axes.edgecolor'] = '#2A2D35'
        plt.rcParams['axes.labelcolor'] = '#FFFFFF'
        plt.rcParams['text.color'] = '#FFFFFF'
        plt.rcParams['xtick.color'] = '#8B8F99'
        plt.rcParams['ytick.color'] = '#8B8F99'
        plt.rcParams['grid.color'] = '#2A2D35'
        plt.rcParams['grid.alpha'] = 0.5
    except Exception:
        pass

def landing_view(request):
    """Redirect landing root to user portal."""
    return redirect('user_portal')

@never_cache
def user_portal_view(request):
    """Handle issue submission GET/POST inside the user portal interface."""
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.raw_text = f"{issue.subject} {issue.body}"
            
            # Run VADER sentiment analysis (same as pandas lambda apply, but single value)
            issue.sentiment_score = analyze_sentiment(issue.raw_text)
            
            # Run rule-based urgency scoring
            urgency_result = calculate_urgency(issue.raw_text, issue.sentiment_score)
            issue.urgency_score = urgency_result['score']
            issue.urgency_level = urgency_result['level']
            
            # Run team classification
            issue.assigned_team = classify_team(issue.raw_text)
            
            # Ensure status is Open for new submissions
            issue.status = 'Open'
            issue.save()
            
            # Add to priority queue
            push_issue(issue_priority_queue, issue.id, issue.urgency_score, issue.created_at)
            
            # Add to search index
            add_to_index(issue_search_index, issue.id, issue.raw_text)
            
            messages.success(request, f"Issue #{issue.id} submitted successfully.")
            return redirect('user_portal')
    else:
        form = IssueForm()
        
    return render(request, 'user_portal.html', {'form': form})

def track_issue_view(request):
    """POST-only request for issue tracking, returns placeholder alert text."""
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id', '').strip()
        # Non-functional mockup tracking query response
        return HttpResponse(f"Issue found: {issue_id} - Status: Open")
    return HttpResponse("Method not allowed", status=405)

@login_required
def developer_dashboard_view(request):
    """Render the main developer dashboard with statistics, charts, and priority queue."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    # Stat cards
    total = Issue.objects.count()
    open_count = Issue.objects.filter(status='Open').count()
    escalated_count = Issue.objects.filter(status='Escalated').count()
    resolved_count = Issue.objects.filter(status='Resolved').count()
    
    # Issue Priority chart data
    priority_counts = Issue.objects.values('urgency_level').annotate(count=Count('id'))
    priority_data = {
        'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0
    }
    for item in priority_counts:
        if item['urgency_level'] in priority_data:
            priority_data[item['urgency_level']] = item['count']
    
    # Issue Status chart data
    status_counts = {
        'Open': open_count,
        'Escalated': escalated_count,
        'Resolved': resolved_count
    }
    
    # Sentiment Overview data
    sentiment_data = {
        'positive': Issue.objects.filter(sentiment_score__gte=0.05).count(),
        'negative': Issue.objects.filter(sentiment_score__lte=-0.05).count(),
        'neutral': Issue.objects.filter(sentiment_score__gt=-0.05, sentiment_score__lt=0.05).count()
    }
    
    # Rebuild priority queue from DB to reflect any manual changes
    issue_priority_queue.clear()
    for iss in Issue.objects.exclude(status='Resolved'):
        push_issue(issue_priority_queue, iss.id, iss.urgency_score, iss.created_at)
    
    # Priority Queue top 5
    top_5 = get_top_n(issue_priority_queue, 5)
    priority_issues = []
    for issue_id, urgency in top_5:
        try:
            issue = Issue.objects.get(id=issue_id)
            priority_issues.append(issue)
        except Issue.DoesNotExist:
            pass
            
    # Recent issues (last 5)
    recent_issues = Issue.objects.all().order_by('-created_at')[:5]
    
    # Search Index metrics
    search_keywords_count = len(issue_search_index)
    search_avg_issues = round(sum(len(v) for v in issue_search_index.values()) / search_keywords_count, 1) if search_keywords_count > 0 else 0
    
    context = {
        'total': total,
        'open_count': open_count,
        'escalated_count': escalated_count,
        'resolved_count': resolved_count,
        'priority_data': priority_data,
        'status_counts': status_counts,
        'sentiment_data': sentiment_data,
        'priority_issues': priority_issues,
        'recent_issues': recent_issues,
        'issues': recent_issues,
        'search_keywords_count': search_keywords_count,
        'search_avg_issues': search_avg_issues,
    }
    return render(request, 'developer_dashboard.html', context)

@login_required
def all_issues_view(request):
    """Render a dedicated full support issue queue view with status stats."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    all_issues = Issue.objects.all().order_by('-created_at')
    
    team_filter = request.GET.get('team')
    if team_filter:
        all_issues = all_issues.filter(assigned_team=team_filter)
    
    total_count = all_issues.count()
    open_count = all_issues.filter(status='Open').count()
    escalated_count = all_issues.filter(status='Escalated').count()
    resolved_count = all_issues.filter(status='Resolved').count()
    
    context = {
        'issues': all_issues,
        'total_count': total_count,
        'open_count': open_count,
        'escalated_count': escalated_count,
        'resolved_count': resolved_count,
    }
    return render(request, 'all_issues.html', context)

@login_required
@never_cache
def issue_detail_view(request, id):
    """Render and process updates (status, assigned team, urgency level, sentiment) for a single issue."""
    issue = get_object_or_404(Issue, id=id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        sentiment_score = request.POST.get('sentiment_score')
        urgency_score = request.POST.get('urgency_score')
        assigned_team = request.POST.get('assigned_team')
        
        # Save Assigned Team Change
        if assigned_team in ['Technical Support', 'Billing', 'Security', 'General Inquiry']:
            issue.assigned_team = assigned_team

        # Save Status Change
        if status in ['Open', 'Escalated', 'Resolved']:
            issue.status = status
            if status == 'Resolved':
                issue.resolved_at = timezone.now()
            else:
                issue.resolved_at = None
                
        # Save Sentiment Score Change
        if sentiment_score is not None:
            try:
                issue.sentiment_score = float(sentiment_score)
            except ValueError:
                pass
                
        # Save Urgency Score mapping
        if urgency_score is not None:
            urgency_map = {
                'Low': 0.25,
                'Medium': 0.5,
                'High': 0.75,
                'Critical': 1.0,
              }
            if urgency_score in urgency_map:
                issue.urgency_score = urgency_map[urgency_score]
                issue.urgency_level = urgency_score  # Keep level in sync
            else:
                try:
                    score_val = float(urgency_score)
                    issue.urgency_score = score_val
                    # Derive level from numeric score
                    if score_val <= 0.25:
                        issue.urgency_level = 'Low'
                    elif score_val <= 0.5:
                        issue.urgency_level = 'Medium'
                    elif score_val <= 0.75:
                        issue.urgency_level = 'High'
                    else:
                        issue.urgency_level = 'Critical'
                except ValueError:
                    pass
                    
        issue.save()
        
        # Rebuild the priority queue so changes are instantly reflected
        issue_priority_queue.clear()
        for iss in Issue.objects.exclude(status='Resolved'):
            push_issue(issue_priority_queue, iss.id, iss.urgency_score, iss.created_at)
        
        # Rebuild search index so changes are reflected
        issue_search_index.clear()
        for iss in Issue.objects.all():
            add_to_index(issue_search_index, iss.id, iss.raw_text)
            
        messages.success(request, f"Issue #{issue.id} details updated successfully.")
        return redirect('issue_detail', id=issue.id)
        
    # Map the current urgency_score float to dropdown value for rendering
    current_urgency_level = "Medium"
    if issue.urgency_score <= 0.25:
        current_urgency_level = "Low"
    elif issue.urgency_score <= 0.5:
        current_urgency_level = "Medium"
    elif issue.urgency_score <= 0.75:
        current_urgency_level = "High"
    else:
        current_urgency_level = "Critical"

    context = {
        'issue': issue,
        'current_urgency_level': current_urgency_level,
    }
    return render(request, 'issue_detail.html', context)

def redirect_submit(request):
    """Redirect legacy submit paths to user portal."""
    return redirect('user_portal')

def redirect_issues(request):
    """Redirect legacy issues path to developer dashboard."""
    return redirect('developer_dashboard')

@never_cache
def role_login(request):
    """Handle GET to render login view and POST to authenticate and authorize based on role selection."""
    error_message = None
    role = request.POST.get('role', 'developer')  # defaults to developer on failed posts/GET
    username_val = ""
    next_url = request.POST.get('next', '').strip() or request.GET.get('next', '').strip()
    
    if request.method == 'POST':
        username_val = request.POST.get('username', '').strip()
        password_val = request.POST.get('password', '')
        
        user = authenticate(request, username=username_val, password=password_val)
        if user is not None:
            if role == 'user':
                if user.is_superuser:
                    login(request, user)
                    return redirect(next_url if next_url else 'user_portal')
                else:
                    error_message = "User portal requires authorized credentials"
            else:  # developer
                if user.is_superuser or user.is_staff:
                    login(request, user)
                    return redirect(next_url if next_url else 'developer_dashboard')
                else:
                    error_message = "Developer portal requires admin privileges"
        else:
            error_message = "Invalid credentials or insufficient permissions"
            
    # GET request setup
    if request.method == 'GET':
        role = 'developer'  # default selection on fresh load
        
    context = {
        'error_message': error_message,
        'role': role,
        'username_val': username_val,
        'next': next_url,
    }
    return render(request, 'login.html', context)

def role_logout(request):
    """Clear session data and redirect user to the landing gate page."""
    logout(request)
    return redirect('landing')

@never_cache
def role_signup(request):
    """Handle GET to render signup form and POST to register new user accounts."""
    error_message = None
    username_val = ""
    email_val = ""
    
    if request.method == 'POST':
        username_val = request.POST.get('username', '').strip()
        email_val = request.POST.get('email', '').strip()
        password_val = request.POST.get('password', '')
        confirm_password_val = request.POST.get('confirm_password', '')
        
        if password_val != confirm_password_val:
            error_message = "Passwords do not match"
        elif User.objects.filter(username=username_val).exists():
            error_message = "Username is already taken"
        else:
            try:
                user = User.objects.create_user(username=username_val, email=email_val, password=password_val)
                # Auto-login the user
                login(request, user)
                messages.success(request, "Registration successful! Welcome to User Issue Resolver.")
                return redirect('user_portal')
            except Exception as e:
                error_message = f"Error creating account: {str(e)}"
                
    context = {
        'error_message': error_message,
        'username_val': username_val,
        'email_val': email_val,
    }
    return render(request, 'signup.html', context)

@login_required
def analytics_view(request):
    """Render the Matplotlib analytics view."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    issues = Issue.objects.all()
    
    crit = issues.filter(urgency_level='Critical').count()
    high = issues.filter(urgency_level='High').count()
    med = issues.filter(urgency_level='Medium').count()
    low = issues.filter(urgency_level='Low').count()

    try:
        if HAS_MATPLOTLIB and plt is not None:
            apply_dark_theme()
            charts_dir = os.path.join(settings.BASE_DIR, 'issues', 'static', 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            # ----------------------------------------------------
            # CHART 1: Issue Volume Trend
            # ----------------------------------------------------
            plt.figure(figsize=(8, 4))
            if issues.exists():
                dates = [t.created_at.date() for t in issues if t.created_at]
                counts = Counter(dates)
                if counts:
                    sorted_dates = sorted(counts.keys())
                    sorted_counts = [counts[d] for d in sorted_dates]
                    plt.plot([str(d) for d in sorted_dates], sorted_counts, color='#5DADE2', marker='o', linewidth=2)
                    plt.fill_between([str(d) for d in sorted_dates], sorted_counts, color='#5DADE2', alpha=0.25)
            plt.title('Issue Volume Trend')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, 'issue_volume.png'), dpi=100)
            plt.close()

            # ----------------------------------------------------
            # CHART 2: Sentiment Distribution
            # ----------------------------------------------------
            plt.figure(figsize=(8, 4))
            pos = issues.filter(sentiment_score__gte=0.05).count()
            neg = issues.filter(sentiment_score__lte=-0.05).count()
            neu = issues.filter(sentiment_score__gt=-0.05, sentiment_score__lt=0.05).count()
            plt.barh(['Neutral', 'Negative', 'Positive'], [neu, neg, pos], color=['#F0B361', '#F07550', '#79AB7B'])
            plt.title('Sentiment Distribution')
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, 'sentiment_distribution.png'), dpi=100)
            plt.close()

            # ----------------------------------------------------
            # CHART 3: Urgency Breakdown
            # ----------------------------------------------------
            plt.figure(figsize=(6, 6))
            data = [crit, high, med, low]
            if sum(data) > 0:
                plt.pie(data, labels=['Critical', 'High', 'Medium', 'Low'], colors=['#FF7F50', '#F07550', '#F0B361', '#79AB7B'], autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.4})
            plt.title('Urgency Breakdown')
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, 'urgency_breakdown.png'), dpi=100)
            plt.close()
            
            # ----------------------------------------------------
            # CHART 4: Resolution Time
            # ----------------------------------------------------
            plt.figure(figsize=(8, 4))
            resolved = issues.filter(status='Resolved', resolved_at__isnull=False).order_by('-resolved_at')[:5]
            if resolved:
                res_labels = [f"#{t.id}" for t in resolved]
                res_durations = [round((t.resolved_at - t.created_at).total_seconds() / 3600.0, 1) for t in resolved]
                plt.bar(res_labels, res_durations, color='#5DADE2')
                plt.ylabel('Hours')
            else:
                plt.text(0.5, 0.5, 'No resolved issues yet', horizontalalignment='center', verticalalignment='center', color='#8B8F99')
            plt.title('Resolution Time Analysis')
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, 'resolution_time.png'), dpi=100)
            plt.close()
    except Exception:
        # Fall back cleanly to pre-rendered charts in serverless / read-only environment
        pass
    
    context = {
        'issue_volume_url': '/static/charts/issue_volume.png',
        'sentiment_dist_url': '/static/charts/sentiment_distribution.png',
        'urgency_breakdown_url': '/static/charts/urgency_breakdown.png',
        'resolution_time_url': '/static/charts/resolution_time.png',
        'urgency_total': sum([crit, high, med, low])
    }
    return render(request, 'analytics.html', context)

@login_required
def team_queue_view(request):
    """Render placeholder Team Queue overview with static issue counts of 0."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    counts = dict(Issue.objects.values_list('assigned_team').annotate(count=Count('id')))
    
    context = {
        'tech_count': counts.get('Technical Support', 0),
        'billing_count': counts.get('Billing', 0),
        'security_count': counts.get('Security', 0),
        'general_count': counts.get('General Inquiry', 0),
    }
    return render(request, 'team_queue.html', context)

@login_required
def download_issues_excel(request):
    """Generate and return styled Excel (.xlsx) file containing all issues."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return redirect('download_issues_csv')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Support Issues"
    
    headers = [
        "ID", "Email Address", "Subject", "Body", "Assigned Team", 
        "Urgency Score", "Sentiment Score", "Status", "Created At", "Resolved At"
    ]
    ws.append(headers)
    
    # Style header row
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E2128", end_color="1E2128", fill_type="solid")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    # Populate data rows
    issues = Issue.objects.all().order_by('-created_at')
    for t in issues:
        created_str = t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
        resolved_str = t.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if t.resolved_at else ""
        ws.append([
            t.id,
            t.customer_email,
            t.subject,
            t.body,
            t.assigned_team,
            t.urgency_score,
            t.sentiment_score,
            t.status,
            created_str,
            resolved_str
        ])
        
    # Auto-adjust column width dimensions
    for col in ws.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 40)
        
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="smartroute_issues.xlsx"'
    wb.save(response)
    return response

@login_required
def next_issue(request):
    """
    Agent clicks 'Next Issue' — pop highest priority from queue.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    while True:
        issue_id = pop_issue(issue_priority_queue)
        if not issue_id:
            # Queue empty
            messages.info(request, "No issues in queue.")
            return redirect('developer_dashboard')
            
        try:
            issue = Issue.objects.get(id=issue_id)
            return redirect('issue_detail', id=issue.id)
        except Issue.DoesNotExist:
            # ID is stale, keep popping
            continue

@login_required(login_url='/login/')
def download_issues_csv(request):
    """Generate and return a CSV file containing all issues."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')

    import csv

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="smartroute_issues.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID", "Email Address", "Subject", "Body", "Assigned Team",
        "Urgency Score", "Sentiment Score", "Status", "Created At", "Resolved At"
    ])

    issues = Issue.objects.all().order_by('-created_at')
    for t in issues:
        created_str = t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
        resolved_str = t.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if t.resolved_at else ""
        writer.writerow([
            t.id,
            t.customer_email,
            t.subject,
            t.body,
            t.assigned_team,
            t.urgency_score,
            t.sentiment_score,
            t.status,
            created_str,
            resolved_str
        ])

    return response

@login_required
def search_issues(request):
    """
    Handle search from developer dashboard.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Developer portal requires admin privileges")
        return redirect('user_portal')
        
    query = request.GET.get('q', '').strip()
    
    if not query:
        return redirect('all_issues')
    
    # Search inverted index
    matching_ids = search_index(issue_search_index, query)
    
    # Support searching by ID (e.g. '12' or 'SR-12' or '#SR-12')
    clean_query = query.lower().replace('#', '')
    if clean_query.isdigit():
        matching_ids.append(int(clean_query))
    elif clean_query.startswith('sr-') and clean_query[3:].isdigit():
        matching_ids.append(int(clean_query[3:]))
    
    # Get issue objects
    issues = Issue.objects.filter(id__in=matching_ids).order_by('-created_at')
    
    context = {
        'issues': issues,
        'query': query,
        'count': len(issues),
    }
    return render(request, 'search_results.html', context)
