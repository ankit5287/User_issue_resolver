from django.contrib import admin
from .models import Issue, SearchIndex, PriorityQueueItem

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_email', 'subject', 'urgency_score', 'status', 'assigned_team', 'created_at')
    list_editable = ('status', 'assigned_team')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_email', 'subject', 'body')

@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    list_display = ('id', 'keyword', 'issue_ids')
    search_fields = ('keyword',)

@admin.register(PriorityQueueItem)
class PriorityQueueItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue_id', 'priority_score', 'created_at')
    search_fields = ('issue_id',)
