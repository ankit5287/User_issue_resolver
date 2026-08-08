import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartroute.settings')
django.setup()

from issues.models import Issue
from issues.queue_manager import issue_priority_queue
from issues.algorithms.priority_queue import get_top_n

issues = Issue.objects.all()
print(f"Total issues: {issues.count()}")

print("\n--- Status Counts ---")
for s in ['Open', 'Escalated', 'Resolved']:
    print(f"  {s}: {issues.filter(status=s).count()}")

print("\n--- Urgency Levels ---")
for u in ['Critical', 'High', 'Medium', 'Low']:
    print(f"  {u}: {issues.filter(urgency_level=u).count()}")

print(f"\n--- Priority Queue (size: {len(issue_priority_queue)}) ---")
top = get_top_n(issue_priority_queue, 5)
for i, u in top:
    try:
        iss = Issue.objects.get(id=i)
        print(f"  #{iss.id} | {iss.subject[:40]} | urgency={iss.urgency_level} | status={iss.status}")
    except Issue.DoesNotExist:
        print(f"  #{i} | STALE (deleted)")

print("\n--- Sample Issues ---")
for iss in issues.order_by('-created_at')[:5]:
    print(f"  #{iss.id} | {iss.subject[:40]} | {iss.urgency_level} | {iss.status} | {iss.customer_email}")
