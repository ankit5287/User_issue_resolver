"""
User Issue Resolver Urgency Scoring Module
Rule-based urgency calculator using keyword matching + sentiment.
"""

def calculate_urgency(text, sentiment_score):
    """
    Calculate urgency score and level from issue text and sentiment.
    
    Args:
        text: Combined subject + body of issue
        sentiment_score: VADER compound score (-1.0 to +1.0)
    
    Returns:
        dict: {'score': int (0-100), 'level': str ('Critical'|'High'|'Medium'|'Low')}
    """
    text_lower = text.lower()
    score = 0
    
    # Critical keywords (+25 each)
    critical_words = [
        'down', 'crash', 'breach', 'hack', 'outage', 'emergency',
        'unauthorized', 'intrusion', 'urgent', 'critical', 'failed',
        'payment', 'refund', 'money', 'deducted', 'charged', 'twice'
    ]
    
    # High keywords (+15 each)
    high_words = [
        'broken', 'error', 'not working', 'slow', 'timeout',
        'not responding', 'bug', 'glitch', 'issue', 'problem'
    ]
    
    # Medium keywords (+5 each)
    medium_words = ['help', 'concern', 'question', 'request']
    
    # Count matches
    for word in critical_words:
        if word in text_lower:
            score += 75
    
    for word in high_words:
        if word in text_lower:
            score += 50
    
    for word in medium_words:
        if word in text_lower:
            score += 5
    
    # Sentiment modifier
    if sentiment_score <= -0.5:
        score += 15
    elif sentiment_score <= -0.2:
        score += 5
    elif sentiment_score >= 0.2:
        score -= 5
    
    # Cap at 100, minimum 0
    score = max(0, min(score, 100))
    
    # Determine level
    if score >= 75:
        level = 'Critical'
    elif score >= 50:
        level = 'High'
    elif score >= 25:
        level = 'Medium'
    else:
        level = 'Low'
    
    return {'score': score, 'level': level}


# Quick test
if __name__ == "__main__":
    test_cases = [
        ("Server crashed and is completely down", -0.85),
        ("How do I reset my password?", 0.44),
        ("Payment failed but money was deducted", -0.61),
        ("Great service, thank you!", 0.85),
        ("UI bug on mobile view", -0.10),
    ]
    
    for text, sentiment in test_cases:
        result = calculate_urgency(text, sentiment)
        print(f"{text[:40]}... -> Score: {result['score']}, Level: {result['level']}")
