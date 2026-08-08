"""
User Issue Resolver Team Classification Module
Rule-based team classifier using keyword dictionaries.
"""

def classify_team(text):
    """
    Classify issue text into one of 4 teams.
    
    Args:
        text: Combined subject + body of issue
    
    Returns:
        str: Team name ('Technical Support' | 'Billing' | 'Security' | 'General Inquiry')
    """
    text_lower = text.lower()
    
    # Team keyword dictionaries
    teams = {
        'Technical Support': [
            'bug', 'error', 'crash', 'ui', 'frontend', 'backend', 'api',
            'database', 'server', 'deploy', 'timeout', '500', '404',
            'not loading', 'broken', 'glitch', 'slow', 'not responding',
            'exception', 'failed'
        ],
        'Billing': [
            'payment', 'refund', 'charge', 'invoice', 'billing', 'subscription',
            'price', 'cost', 'money', 'card', 'transaction', 'failed payment',
            'deducted', 'charged', 'twice', 'overcharged'
        ],
        'Security': [
            'hack', 'breach', 'unauthorized', 'login failed', 'suspicious',
            'virus', 'malware', 'phishing', 'stolen', 'access denied',
            'intrusion', 'password stolen', 'account locked', 'unusual activity'
        ],
        'General Inquiry': []  # Default fallback
    }
    
    # Count matches for each team
    scores = {}
    for team, keywords in teams.items():
        count = 0
        for keyword in keywords:
            if keyword in text_lower:
                count += 1
        scores[team] = count
    
    # Find team with highest score
    best_team = max(scores, key=scores.get)
    
    # If no matches at all, default to General Inquiry
    if scores[best_team] == 0:
        return 'General Inquiry'
    
    return best_team


# Quick test
if __name__ == "__main__":
    test_cases = [
        "Server crashed, urgent help needed",
        "Payment failed but money was deducted",
        "Suspicious login from unknown device",
        "How do I reset my password?",
        "Database breach detected, unauthorized access",
        "UI bug on mobile view",
        "Feature request: dark mode",
    ]
    
    for text in test_cases:
        team = classify_team(text)
        print(f"{text[:40]}... → {team}")
