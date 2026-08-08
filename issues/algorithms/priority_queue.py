"""
User Issue Resolver Priority Queue Module
Uses Python heapq for efficient issue prioritization.
"""

import heapq

def create_queue():
    """Create and return an empty priority queue (just a list)."""
    return []

def push_issue(queue, issue_id, urgency_score, timestamp):
    """
    Add a issue to the priority queue.
    
    Args:
        queue: The heap list
        issue_id: int
        urgency_score: int (0-100)
        timestamp: datetime object (issue.created_at)
    
    The heap stores tuples: (-urgency, timestamp, issue_id)
    Negative urgency because heapq is a min-heap.
    """
    # heapq is min-heap, so negate urgency for max-heap behavior
    priority = (-urgency_score, timestamp, issue_id)
    heapq.heappush(queue, priority)

def pop_issue(queue):
    """
    Remove and return the highest priority issue ID.
    
    Returns:
        issue_id (int) or None if queue is empty
    """
    if not queue:
        return None
    priority, timestamp, issue_id = heapq.heappop(queue)
    return issue_id

def peek_top(queue):
    """
    Look at the highest priority issue without removing it.
    
    Returns:
        issue_id (int) or None if queue is empty
    """
    if not queue:
        return None
    return queue[0][2]  # issue_id is third element

def get_top_n(queue, n=5):
    """
    Get top N issues without removing them.
    Returns list of (issue_id, urgency_score) tuples.
    """
    # heapq.nsmallest returns n smallest items (which = highest urgency due to negative)
    top_items = heapq.nsmallest(n, queue)
    result = []
    for priority, timestamp, issue_id in top_items:
        result.append((issue_id, -priority))  # negate back to positive urgency
    return result


# Quick test
if __name__ == "__main__":
    from datetime import datetime
    
    q = create_queue()
    
    # Simulate issues arriving
    push_issue(q, 1, 90, datetime(2026, 7, 15, 10, 0))
    push_issue(q, 2, 75, datetime(2026, 7, 15, 9, 0))
    push_issue(q, 3, 90, datetime(2026, 7, 15, 9, 30))  # same urgency, older than #1
    
    print("Queue:", q)
    
    # Should pop issue 3 first (urgency 90, older timestamp)
    next_id = pop_issue(q)
    print(f"First: Issue #{next_id}")  # 3
    
    next_id = pop_issue(q)
    print(f"Second: Issue #{next_id}")  # 1
    
    next_id = pop_issue(q)
    print(f"Third: Issue #{next_id}")  # 2
