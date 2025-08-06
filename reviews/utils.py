# reviews/utils.py
import re
from textblob import TextBlob


def normalize_string(text):
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove all non-alphanumeric characters (keep spaces)
    text = re.sub(r'[^\w\s]', '', text)
    # Replace multiple spaces with a single space and strip leading/trailing spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_title(title):
    """Normalizes a book title for consistent matching."""
    return re.sub(r'\(.*\)', '', title).strip().lower()

def normalize_author(author):
    """Normalizes an author's name for consistent matching."""
    if not author:
        return ''
    # Remove common suffixes like '(Author)' or '(Goodreads Author)'
    author = re.sub(r'\s*\(.*\)', '', author)
    # Remove common connecting words like 'by'
    author = re.sub(r'\s+by\s+', ' ', author)
    return author.strip().lower()

def get_sentiment_label(text):
    """
    Performs sentiment analysis on a given text using TextBlob.
    Returns a sentiment label ('Positive', 'Negative', 'Neutral') and the polarity score.
    """
    if not text:
        return 'Neutral', 0.0

    analysis = TextBlob(text)
    score = analysis.sentiment.polarity
    
    if score > 0.1:
        return 'Positive', score
    elif score < -0.1:
        return 'Negative', score
    else:
        return 'Neutral', score