from django.apps import AppConfig

class IssuesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'issues'

    def ready(self):
        # Rebuild priority queue from database on startup
        from .models import Issue
        from .algorithms.priority_queue import push_issue
        from .queue_manager import issue_priority_queue
        from .algorithms.search_index import add_to_index
        from .search_manager import issue_search_index
        
        try:
            # Rebuild priority queue
            open_issues = Issue.objects.filter(status__in=['Open', 'Escalated'])
            for issue in open_issues:
                push_issue(issue_priority_queue, issue.id, issue.urgency_score, issue.created_at)
                
            # Rebuild search index
            for issue in Issue.objects.all():
                add_to_index(issue_search_index, issue.id, issue.raw_text)
        except Exception:
            # Table might not exist yet during initial migrations
            pass
