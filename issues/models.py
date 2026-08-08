from django.db import models

class Issue(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Resolved', 'Resolved'),
        ('Escalated', 'Escalated'),
    ]
    customer_email = models.EmailField()
    subject = models.CharField(max_length=255, default='No Subject')
    body = models.TextField()
    raw_text = models.TextField(blank=True, default='')
    urgency_score = models.IntegerField(default=0, blank=True, null=True)
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('Critical', 'Critical'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
        ],
        default='Low',
        blank=True
    )
    sentiment_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    
    TEAM_CHOICES = [
        ('Technical Support', 'Technical Support'),
        ('Billing', 'Billing'),
        ('Security', 'Security'),
        ('General Inquiry', 'General Inquiry'),
    ]
    assigned_team = models.CharField(max_length=50, choices=TEAM_CHOICES, default='General Inquiry', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.status})"

    @property
    def sentiment_category(self):
        if self.sentiment_score >= 0.05:
            return 'Positive'
        elif self.sentiment_score < -0.05:
            return 'Negative'
        return 'Neutral'

class SearchIndex(models.Model):
    keyword = models.CharField(max_length=100)
    issue_ids = models.TextField(default="[]")  # Stores JSON list of integers as string

    def __str__(self):
        return f"{self.keyword}: {self.issue_ids}"

class PriorityQueueItem(models.Model):
    issue_id = models.IntegerField(unique=True)
    priority_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Issue #{self.issue_id} (Priority: {self.priority_score})"
