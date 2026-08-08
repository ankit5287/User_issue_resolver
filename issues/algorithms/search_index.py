"""
User Issue Resolver Inverted Search Index Module
Custom dictionary-based inverted index for fast issue search.
"""

def build_index():
    """Create and return empty inverted index."""
    return {}

def add_to_index(index, issue_id, text):
    """
    Add a issue's text to the inverted index.
    
    Args:
        index: The inverted index dictionary
        issue_id: int
        text: Combined subject + body
    """
    # Simple tokenization: lowercase, split by spaces, remove punctuation
    words = text.lower().replace(',', '').replace('.', '').replace('!', '').replace('?', '').split()
    
    for word in words:
        if word not in index:
            index[word] = set()
        index[word].add(issue_id)

def search_index(index, query):
    """
    Search the inverted index for issues matching query.
    Uses AND logic: all query words must be present.
    
    Args:
        index: The inverted index dictionary
        query: Search string from user
    
    Returns:
        list: Issue IDs that match all query words
    """
    if not query or not query.strip():
        return []
    
    # Tokenize query same way as index
    words = query.lower().replace(',', '').replace('.', '').replace('!', '').replace('?', '').split()
    
    if not words:
        return []
    
    # Start with issues matching first word
    result = index.get(words[0], set()).copy()
    
    # Intersect with remaining words (AND search)
    for word in words[1:]:
        result &= index.get(word, set())
        if not result:  # Early exit if no matches
            break
    
    return list(result)


# Quick test
if __name__ == "__main__":
    idx = build_index()
    
    add_to_index(idx, 1, "Server crashed urgent help")
    add_to_index(idx, 2, "Payment failed need refund")
    add_to_index(idx, 3, "Server down again help needed")
    
    print("Index:", {k: list(v) for k, v in idx.items()})
    
    print("Search 'server':", search_index(idx, "server"))           # [1, 3]
    print("Search 'server crashed':", search_index(idx, "server crashed"))  # [1]
    print("Search 'payment refund':", search_index(idx, "payment refund"))   # [2]
    print("Search 'help':", search_index(idx, "help"))                 # [1, 3]
    print("Search 'notfound':", search_index(idx, "notfound"))         # []
