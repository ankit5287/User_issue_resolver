from .algorithms.priority_queue import create_queue

# Global queue instance (lives as long as server runs)
# Note: This resets on server restart. For production, you'd rebuild from DB.
issue_priority_queue = create_queue()
