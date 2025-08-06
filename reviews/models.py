from django.db import models
from django.db.models import Avg

class Book(models.Model):
    title = models.CharField(max_length=255)
    normalized_title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    normalized_author = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    published_date = models.CharField(max_length=255, blank=True, null=True)
    average_rating = models.FloatField(blank=True, null=True)
    num_ratings = models.IntegerField(blank=True, null=True)
    num_reviews = models.IntegerField(blank=True, null=True)
    cover_image_url = models.URLField(max_length=2000, blank=True, null=True)
    goodreads_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    goodreads_url = models.URLField(max_length=2000, blank=True, null=True)
    google_books_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    info_link = models.URLField(max_length=2000, blank=True, null=True)
    isbn = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def display_average_rating(self):
        return f"{self.average_rating:.2f}" if self.average_rating is not None else "N/A"

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    source_website = models.CharField(max_length=50, null=True, blank=True)
    review_url = models.URLField(max_length=500, null=True, blank=True)
    reviewer_name = models.CharField(max_length=255, null=True, blank=True) # <-- Add this line
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True) # Ensure this field exists
    review_text = models.TextField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True) # <-- Add this line
    sentiment_label = models.CharField(max_length=20, null=True, blank=True) # <-- Add this line
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.book.title} by {self.reviewer_name or 'Anonymous'}"
