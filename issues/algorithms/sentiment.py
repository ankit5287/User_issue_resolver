"""
VADER Sentiment Analysis for User Issue Resolver issues.
Includes fail-safe fallback for serverless cloud environments (Vercel).
"""

import nltk

_sia = None

def get_sia():
    global _sia
    if _sia is None:
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except Exception:
            try:
                nltk.download('vader_lexicon', download_dir='/tmp/nltk_data', quiet=True)
                if '/tmp/nltk_data' not in nltk.data.path:
                    nltk.data.path.append('/tmp/nltk_data')
            except Exception:
                pass
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            _sia = SentimentIntensityAnalyzer()
        except Exception:
            _sia = False
    return _sia


def analyze_sentiment(text):
    """
    VADER sentiment analysis with robust fallback for serverless environments.
    Returns compound score (-1.0 to +1.0).
    """
    if not text or not text.strip():
        return 0.0
    try:
        sia = get_sia()
        if sia:
            return sia.polarity_scores(text)['compound']
    except Exception:
        pass

    # Basic dictionary fallback if NLTK lexicon download fails in serverless sandbox
    lower_text = text.lower()
    pos_words = {'good', 'great', 'awesome', 'excellent', 'fixed', 'resolved', 'thanks', 'happy', 'working'}
    neg_words = {'bad', 'error', 'fail', 'broken', 'issue', 'crash', 'urgent', 'bug', 'down', 'slow', 'cannot'}
    pos_count = sum(1 for w in pos_words if w in lower_text)
    neg_count = sum(1 for w in neg_words if w in lower_text)
    if pos_count > neg_count:
        return 0.5
    elif neg_count > pos_count:
        return -0.5
    return 0.0


def get_sentiment_category(score):
    """
    Categorize sentiment score into Positive/Neutral/Negative.
    """
    if score >= 0.05:
        return 'Positive'
    elif score <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'


def get_sentiment_analytics(issues_qs):
    """
    Batch sentiment analytics for Issue querysets.
    Returns dict with positive, negative, neutral counts.
    """
    pos, neg, neu = 0, 0, 0
    for score in issues_qs.values_list('sentiment_score', flat=True):
        if score is not None:
            if score >= 0.05:
                pos += 1
            elif score <= -0.05:
                neg += 1
            else:
                neu += 1
    return {
        'positive': pos,
        'negative': neg,
        'neutral': neu,
    }
