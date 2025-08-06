# In reviews/sentiment_analyzer.py

import re
from .models import Review

# A simple list of positive and negative words
POSITIVE_WORDS = {'love', 'great', 'excellent', 'amazing', 'perfect', 'beautiful', 'wonderful', 'enjoyed', 'best'}
NEGATIVE_WORDS = {'hate', 'bad', 'terrible', 'awful', 'disappointing', 'boring', 'worst', 'confusing', 'didn\'t like'}

def run_sentiment_analysis_on_reviews(reviews):
    """
    Analyzes the sentiment of a list of reviews and updates the database.
    """
    updated_reviews = []
    for review in reviews:
        text = review.review_text.lower()
        
        # Tokenize the text into words
        words = re.findall(r'\w+', text)
        
        positive_score = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_score = sum(1 for word in words if word in NEGATIVE_WORDS)
        
        sentiment_score = positive_score - negative_score

        if sentiment_score > 0:
            review.sentiment_label = 'positive'
        elif sentiment_score < 0:
            review.sentiment_label = 'negative'
        else:
            review.sentiment_label = 'neutral'
        
        review.sentiment_score = sentiment_score
        updated_reviews.append(review)
    
    # Bulk update the reviews to save the changes
    Review.objects.bulk_update(updated_reviews, ['sentiment_label', 'sentiment_score'])
    
    return updated_reviews