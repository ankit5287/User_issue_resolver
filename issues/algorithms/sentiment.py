"""
VADER Sentiment Analysis for User Issue Resolver issues.

Uses the same approach as the pandas DataFrame lambda apply method:
    df['VADER Sentiment'] = df['Body'].apply(lambda x: sia.polarity_scores(x)['compound'])

But adapted for single issue analysis on submission.
"""

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

_sia = None

def get_sia():
    global _sia
    if _sia is None:
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon', download_dir='/tmp/nltk_data', quiet=True)
            if '/tmp/nltk_data' not in nltk.data.path:
                nltk.data.path.append('/tmp/nltk_data')
        _sia = SentimentIntensityAnalyzer()
    return _sia



def analyze_sentiment(text):
    """
    Simple VADER sentiment analysis.
    Returns compound score (-1.0 to +1.0).
    Same approach as: df['Body'].apply(lambda x: sia.polarity_scores(x)['compound'])
    """
    if not text or not text.strip():
        return 0.0
    return get_sia().polarity_scores(text)['compound']


def get_sentiment_category(score):
    """
    Categorize sentiment score into Positive/Neutral/Negative.
    Same logic as: df['category'] = df['score'].apply(
        lambda x: 'Positive' if x >= 0.05 else ('Negative' if x <= -0.05 else 'Neutral')
    )
    """
    if score >= 0.05:
        return 'Positive'
    elif score <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'


def get_sentiment_analytics(issues_qs):
    """
    Batch sentiment analytics using pandas DataFrame approach.
    Same pattern as user's original code using df.apply(lambda ...).
    
    Args:
        issues_qs: Django QuerySet of Issue objects
    
    Returns:
        dict with positive, negative, neutral counts
    """
    import pandas as pd

    data = list(issues_qs.values('id', 'raw_text', 'sentiment_score'))
    if not data:
        return {'positive': 0, 'negative': 0, 'neutral': 0}

    df = pd.DataFrame(data)

    # Categorize using pandas lambda apply (same as user's approach)
    df['category'] = df['sentiment_score'].apply(
        lambda x: 'Positive' if x >= 0.05 else ('Negative' if x <= -0.05 else 'Neutral')
    )

    # Count for chart
    counts = df['category'].value_counts()
    return {
        'positive': int(counts.get('Positive', 0)),
        'negative': int(counts.get('Negative', 0)),
        'neutral': int(counts.get('Neutral', 0)),
    }
