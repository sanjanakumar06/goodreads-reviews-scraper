import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'book_reviews_project.settings')
django.setup()

from reviews.models import Book

def delete_duplicate_books():
    print("Finding and deleting duplicate books...")
    duplicates = Book.objects.values('normalized_title', 'normalized_author').annotate(count=Count('id')).filter(count__gt=1)

    if not duplicates:
        print("No duplicate books found.")
        return

    for item in duplicates:
        title = item['normalized_title']
        author = item['normalized_author']

        # Get all the duplicate books for this title/author combination
        books_to_delete = Book.objects.filter(normalized_title=title, normalized_author=author).order_by('id')

        # Keep the first book and delete the rest
        for book in books_to_delete[1:]:
            book.delete()

        print(f"Deleted duplicates for: {title} by {author}")

    print("Finished cleaning up duplicate books.")

if __name__ == "__main__":
    delete_duplicate_books()