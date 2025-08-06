# In reviews/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Review
from .scraper import find_goodreads_id_from_title_author, get_goodreads_book_metadata, get_goodreads_reviews, create_or_update_book_record, save_goodreads_reviews_to_db
from django.db import transaction
import time

def book_list(request):
    books = Book.objects.all().order_by('title')
    return render(request, 'reviews/book_list.html', {'books': books})

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all().order_by('-review_date')

    # New code to calculate sentiment data for the template
    total_reviews = reviews.count()
    sentiment_data = {
        'total': total_reviews,
        'positive_percent': 0,
        'neutral_percent': 0,
        'negative_percent': 0,
    }
    if total_reviews > 0:
        positive_count = reviews.filter(sentiment_label='Positive').count()
        neutral_count = reviews.filter(sentiment_label='Neutral').count()
        negative_count = reviews.filter(sentiment_label='Negative').count()

        sentiment_data['positive_percent'] = (positive_count / total_reviews) * 100
        sentiment_data['neutral_percent'] = (neutral_count / total_reviews) * 100
        sentiment_data['negative_percent'] = (negative_count / total_reviews) * 100
    
    return render(request, 'reviews/book_detail.html', {'book': book, 'reviews': reviews, 'sentiment_data': sentiment_data})

def clean_title(title, author):
    # Remove 'by [author]' or any ' by ...' at the end of the title
    lower_title = title.lower()
    if author and f"by {author.lower()}" in lower_title:
        split_idx = lower_title.index(f"by {author.lower()}")
        return title[:split_idx].strip()
    if ' by ' in lower_title:
        split_idx = lower_title.index(' by ')
        return title[:split_idx].strip()
    return title.strip()


def scrape_book(request):

    if request.method == 'POST':
        # CORRECTED LINES: Use .get('key', '') to ensure a string is always returned
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        title = clean_title(title, author)

        
        # You can keep the `scrape_count` logic as it was
        max_reviews = int(request.POST.get('scrape_count', 25))

        # Add a check to ensure at least a title is provided
        if not title:
            print("ERROR: A book title is required.")
            return redirect('reviews:book_list')


        goodreads_id = find_goodreads_id_from_title_author(title, author)
        
        if not goodreads_id:
            print(f"Could not find a Goodreads ID for '{title}' by {author}")
            return redirect('reviews:book_list')

        book_metadata = get_goodreads_book_metadata(goodreads_id)
        
        if not book_metadata or not book_metadata.get('title'):
            print(f"Could not scrape metadata for Goodreads ID {goodreads_id}")
            return redirect('reviews:book_list')
        
        try:
            with transaction.atomic():
                book_obj = create_or_update_book_record(book_metadata, 'goodreads')
        except Exception as e:
            print(f"Error saving book metadata: {e}")
            return redirect('reviews:book_list')

        reviews_data = get_goodreads_reviews(goodreads_id, max_reviews)

        if reviews_data:
            save_goodreads_reviews_to_db(book_obj, reviews_data)

        return redirect('reviews:book_detail', pk=book_obj.pk)

    books = Book.objects.all()
    return render(request, 'reviews/scrape_form.html', {'books': books})

