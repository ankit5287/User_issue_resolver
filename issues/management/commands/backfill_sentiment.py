from django.core.management.base import BaseCommand
from issues.models import Issue
from issues.algorithms.sentiment import analyze_sentiment

class Command(BaseCommand):
    help = 'Backfill sentiment_score for existing issues using VADER.'

    def handle(self, *args, **options):
        issues = Issue.objects.all()
        count = 0
        for issue in issues:
            # Reconstruct raw_text if it's empty
            if not issue.raw_text:
                issue.raw_text = f"{issue.subject} {issue.body}"
            
            # Compute sentiment
            score = analyze_sentiment(issue.raw_text)
            issue.sentiment_score = score
            issue.save(update_fields=['raw_text', 'sentiment_score'])
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully backfilled sentiment scores for {count} issues.'))
