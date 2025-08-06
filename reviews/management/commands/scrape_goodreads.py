from django.core.management.base import BaseCommand, CommandError
from reviews.scraper import scrape_goodreads_book_reviews
from reviews.models import Book # Import the Book model if you want to scrape all existing books

class Command(BaseCommand):
    help = 'Scrapes reviews for a given Goodreads book ID or for all existing books.'

    def add_arguments(self, parser):
        # Optional: Allow passing a specific goodreads_id as an argument
        parser.add_argument('goodreads_id', nargs='?', type=str,
                            help='The Goodreads book ID to scrape. If not provided, all existing books will be updated.')
        parser.add_argument('--max-pages', type=int, default=10,
                            help='Maximum number of review pages to scrape per book. Default is 10.')

    def handle(self, *args, **options):
        goodreads_id = options['goodreads_id']
        max_pages = options['max_pages']

        if goodreads_id:
            self.stdout.write(self.style.SUCCESS(f'Initiating scrape for Goodreads ID: {goodreads_id}'))
            try:
                scrape_goodreads_book_reviews(goodreads_id, max_pages=max_pages)
                self.stdout.write(self.style.SUCCESS(f'Successfully scraped reviews for Goodreads ID: {goodreads_id}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error scraping Goodreads ID {goodreads_id}: {e}'))
                raise CommandError(f'Scraping failed for Goodreads ID {goodreads_id}')
        else:
            self.stdout.write(self.style.SUCCESS('Initiating scrape for all existing books in the database.'))
            books = Book.objects.all()
            if not books.exists():
                self.stdout.write(self.style.WARNING('No books found in the database to scrape.'))
                return

            for book in books:
                self.stdout.write(self.style.SUCCESS(f'Scraping reviews for book "{book.title}" (ID: {book.goodreads_id})...'))
                try:
                    # Pass the goodreads_id from the book object
                    scrape_goodreads_book_reviews(book.goodreads_id, max_pages=max_pages)
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated reviews for "{book.title}"'))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error updating reviews for "{book.title}" (ID: {book.goodreads_id}): {e}'))
                    # Continue to the next book even if one fails
            self.stdout.write(self.style.SUCCESS('Finished scraping for all existing books.'))