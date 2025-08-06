# Goodreads Book Review Scraper & Sentiment Dashboard

This Django web application enables users to search for books, scrape reviews from Goodreads, analyze review sentiment, and visualize review/book metadata in a modern, user-friendly dashboard.

## Features

- **Book Search & Metadata**: Search for books by title and author, and display detailed information (cover, description, avg rating, number of ratings/reviews).
- **Automated Goodreads Scraping**: Scrape batches of reviews for any book from Goodreads, including support for “Show more reviews” pagination and scraping all available reviews.
- **Duplicate-Free Review Storage**: Ingests and deduplicates reviews based on reviewer, date, and text chunk.
- **Reviewer Info**: Extracts reviewer name and review date for each review (displayed in the UI).
- **Sentiment Analysis**: Automatically analyzes scraped reviews and displays the positive/neutral/negative split in an interactive progress bar.
- **Beautiful Book & Review Display**: Bootstrap-based UI, card-based reviews with reviewer/date/rating/badges, and responsive “See more/less” for long reviews.
- **(Optional) Multi-source Extensibility**: Ready for future support for multiple review providers or custom review uploads.
- **Robust Error Handling & Deduplication**: Graceful failures if Goodreads structure changes, and robust logic to prevent duplicated reviews or books.

## Setup Instructions

### 1. Clone this repository

git clone https://github.com/sanjanakumar06/goodreads-review-scraper.git
cd goodreads-review-scraper


### 2. Create and Activate a Virtual Environment

python3 -m venv venv
source venv/bin/activate


### 3. Install Requirements

pip install -r requirements.txt


Be sure you have:
- Django
- Selenium
- BeautifulSoup4
- requests
- python-decouple (optional, for settings)
- Any other packages listed in `requirements.txt`

You also need [Google Chrome](https://www.google.com/chrome/) and [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) installed for Selenium.

### 4. Database Setup

python manage.py makemigrations
python manage.py migrate


Create a superuser for Django Admin (optional):

python manage.py createsuperuser


### 5. Run the Development Server


Then open [http://127.0.0.1:8000/reviews/](http://127.0.0.1:8000/reviews/) in your browser.

## Usage

1. **Search/Add a Book:**  
   Use the search form or dashboard to find a book. Review metadata and cover art are auto-fetched.
2. **Scrape Reviews:**  
   Click “Scrape Goodreads Reviews,” select the number of reviews (or “All available”), and reviews will be imported and analyzed.
3. **View Sentiment & Analytics:**  
   See a progress bar breakdown for overall sentiment. Each review card shows reviewer name, date, rating, and supports a “See more/less” toggle for easier browsing.

## Key Files & Structure

- `reviews/models.py`: Book and Review models.
- `reviews/views.py`: All main Django views—scraping, detail, dashboard.
- `reviews/templates/reviews/`: Page templates, especially `book_detail.html`.
- `reviews/scraper.py`: Core scraping logic (Selenium + BeautifulSoup), including robust pagination and deduplication.

## Troubleshooting

- **Selenium/Chromedriver not found:**  
  Ensure Chrome and the appropriate ChromeDriver (matching your Chrome version) are installed and on your PATH.
- **Can’t scrape more than 30 reviews at a time:**  
  Goodreads rate-limits or page-swaps reviews rather than appending (see code/design notes).
- **Internal Server Error:**  
  Check for duplicate `{% block title %}` or other template mistakes, and ensure dependencies are correctly installed.

## Potential Future Enhancements

- User authentication
- Goodreads API fallback (note: API does not include full review text)
- Caching, async scraping
- Support for multi-source review aggregation

## License

MIT License (add your preferred license here)

## Credits

- Author: Sanjana Kumar
- [Goodreads.com](https://www.goodreads.com/) (data source, per their TOS)
- Bootstrap (frontend styling)

