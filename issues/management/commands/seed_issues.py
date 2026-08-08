import random
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from issues.models import Issue

from issues.algorithms.sentiment import analyze_sentiment
from issues.algorithms.urgency import calculate_urgency
from issues.algorithms.team_classifier import classify_team

class Command(BaseCommand):
    help = 'Seed realistic sample issues for development'

    def handle(self, *args, **options):
        issue_data = [
            {"subject": "Login page not loading after update", "team": "Technical Support", "status": "Open"},
            {"subject": "Payment failed but money deducted", "team": "Billing", "status": "Escalated"},
            {"subject": "How to reset my password?", "team": "General Inquiry", "status": "Open"},
            {"subject": "Suspicious login from unknown device", "team": "Security", "status": "Open"},
            {"subject": "API returning 500 error on checkout", "team": "Technical Support", "status": "Open"},
            {"subject": "Refund request for order #12345", "team": "Billing", "status": "Open"},
            {"subject": "Database connection timeout", "team": "General Inquiry", "status": "Escalated"},
            {"subject": "UI button misaligned on mobile", "team": "Technical Support", "status": "Resolved"},
            {"subject": "Unauthorized charge on my card", "team": "Billing", "status": "Escalated"},
            {"subject": "Need help with API documentation", "team": "General Inquiry", "status": "Open"},
            {"subject": "Server down for 2 hours", "team": "General Inquiry", "status": "Escalated"},
            {"subject": "Feature request: dark mode", "team": "General Inquiry", "status": "Open"},
            {"subject": "Phishing email received", "team": "Security", "status": "Open"},
            {"subject": "Invoice not generated", "team": "Billing", "status": "Open"},
            {"subject": "Slow page load times", "team": "Technical Support", "status": "Open"},
            {"subject": "Account locked after failed attempts", "team": "Security", "status": "Open"},
            {"subject": "Deployment failed on production", "team": "Technical Support", "status": "Escalated"},
            {"subject": "How to integrate webhook?", "team": "General Inquiry", "status": "Resolved"},
            {"subject": "Double charged for subscription", "team": "Billing", "status": "Open"},
            {"subject": "Memory leak in application", "team": "Technical Support", "status": "Open"},
            {"subject": "SSL certificate expired", "team": "Security", "status": "Escalated"},
            {"subject": "Export data to CSV not working", "team": "Technical Support", "status": "Open"}
        ]

        emails = ["user1@example.com", "user2@gmail.com", "user3@yahoo.com", "user4@test.com", "developer5@smartroute.io"]
        bodies = [
            "Please investigate this behavior immediately.",
            "I tried multiple times but still got the same issue.",
            "This is blocking our team's daily operations.",
            "Is there any workaround for this problem?",
            "Refer to the attachments for error traces."
        ]

        # Clear existing issues to ensure clean state
        Issue.objects.all().delete()
        
        updated_count = 0
        created_count = 0
        for item in issue_data:
            subj = item["subject"]
            email = random.choice(emails)
            body = random.choice(bodies)
            raw_text = f"{subj} {body}"
            status = item["status"]
            
            # Compute real scores (Run algorithms)
            sentiment_score = analyze_sentiment(raw_text)
            urgency_result = calculate_urgency(raw_text, sentiment_score)
            urgency_score = urgency_result['score']
            urgency_level = urgency_result['level']
            assigned_team = classify_team(raw_text)
            
            # Date calculations (past 7 days)
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            created_at = timezone.now() - datetime.timedelta(days=days_ago, hours=hours_ago)
            
            resolved_at = None
            if status in ['Resolved', 'Escalated']:
                resolved_at = created_at + datetime.timedelta(hours=random.randint(1, 48))
                
            issue = Issue.objects.create(
                customer_email=email,
                subject=subj,
                body=body,
                raw_text=raw_text,
                status=status,
                assigned_team=assigned_team,
                urgency_score=urgency_score,
                urgency_level=urgency_level,
                sentiment_score=sentiment_score
            )
            
            # Force custom date bypass auto_now_add
            Issue.objects.filter(id=issue.id).update(created_at=created_at, resolved_at=resolved_at)
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Successfully cleared DB and created {created_count} issues using all algorithms."))
