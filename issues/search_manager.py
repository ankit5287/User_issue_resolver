from .algorithms.search_index import build_index

# Global inverted index (rebuilds on server start)
issue_search_index = build_index()
