# In reviews/scraper.py

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import os
import django
import random
from urllib.parse import quote_plus
from decimal import Decimal, InvalidOperation

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from nltk.sentiment import SentimentIntensityAnalyzer
from .utils import normalize_title, normalize_author
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "book_reviews_project.settings")
django.setup()

from reviews.models import Book, Review

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

sid = SentimentIntensityAnalyzer()

def find_goodreads_id_from_title_author(title, author=None):
    """
    Searches Goodreads and finds the best matching book ID based on title and author.
    This version includes filters to ignore non-book results like Study Guides.
    """
    search_query = f"{title} {author}" if author else title
    url = f"https://www.goodreads.com/search?q={quote_plus(search_query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"[DEBUG] Searching Goodreads with query: '{search_query}'")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        search_results_container = soup.find('table', class_='tableList')
        if not search_results_container:
            print("[INFO] No search results table found. Returning None.")
            return None
            
        search_results = search_results_container.find_all('tr')
        best_match_id = None
        best_score = -1
        normalized_target_title = normalize_title(title)
        normalized_target_author = normalize_author(author) if author else None

        for result_tr in search_results:
            result_link = result_tr.find('a', class_='bookTitle', href=True)
            if not result_link:
                continue

            result_title = result_link.get_text(strip=True)
            if 'study guide' in result_title.lower() or 'summary' in result_title.lower():
                continue
            gid_match = re.search(r'/book/show/(\d+)', result_link['href'])
            if not gid_match:
                continue
            gid = gid_match.group(1)
            author_element = result_tr.find('a', class_='authorName')
            result_author = author_element.get_text(strip=True) if author_element else ''
            score = 0
            normalized_result_title = normalize_title(result_title)
            normalized_result_author = normalize_author(result_author)
            
            if normalized_target_title == normalized_result_title:
                score += 10
            elif normalized_target_title in normalized_result_title:
                    score += 5
            
            if normalized_target_author and normalized_target_author == normalized_result_author:
                score += 10
            elif normalized_target_author and normalized_target_author in normalized_result_author:
                score += 5
            
            if score > best_score:
                best_score = score
                best_match_id = gid

        if best_match_id and best_score > 0:
            print(f"[INFO] Best match found with score {best_score}. Goodreads ID: {best_match_id}")
            return best_match_id
        else:
            print("[INFO] No good match found. Returning None.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] HTTP request failed for Goodreads search: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during Goodreads ID lookup: {e}")
        return None

def normalize_goodreads_book_data(raw):
    return {
        'title': raw.get('title'),
        'author': raw.get('author'),
        'average_rating': raw.get('average_rating'),
        'num_ratings': raw.get('num_ratings'),
        'num_reviews': raw.get('num_reviews'),
        'cover_image_url': raw.get('cover_image_url'),
        'goodreads_id': raw.get('goodreads_id'),
        'goodreads_url': raw.get('goodreads_url'),
        'description': raw.get('description'),
    }

def filter_to_model_fields(data, model):
    model_fields = {field.name for field in model._meta.get_fields()}
    return {k: v for k, v in data.items() if k in model_fields}

def create_or_update_book_record(raw_data, source_platform):
    if source_platform == 'goodreads':
        book_data = normalize_goodreads_book_data(raw_data)
    else:
        raise ValueError(f"Unknown source platform: {source_platform}")
    
    if 'average_rating' in book_data and isinstance(book_data['average_rating'], float):
        try:
            book_data['average_rating'] = Decimal(str(book_data['average_rating']))
        except InvalidOperation:
            book_data['average_rating'] = None

    book_data = filter_to_model_fields(book_data, Book)
    title = book_data.get('title')
    author = book_data.get('author')
    existing_book = None
    if source_platform == 'goodreads' and book_data.get('goodreads_id'):
        existing_book = Book.objects.filter(goodreads_id=book_data['goodreads_id']).first()
    if not existing_book and title:
        norm_title = normalize_title(title)
        norm_author = normalize_author(author) if author else ""
        q = {'title__iexact': norm_title}
        if norm_author:
            q['author__iexact'] = norm_author
        existing_book = Book.objects.filter(**q).first()

    if existing_book:
        updated = False
        for k, v in book_data.items():
            if v is not None and getattr(existing_book, k) in (None, ''):
                setattr(existing_book, k, v)
                updated = True
        if updated:
            existing_book.save()
            print(f"DEBUG: Updated existing book '{existing_book.title}' from {source_platform}")
        return existing_book
    else:
        book = Book.objects.create(**book_data)
        print(f"DEBUG: Created new book '{book.title}' from {source_platform}")
        return book

def get_goodreads_book_metadata(goodreads_id):
    """Scrapes book metadata from the main book page using requests."""
    book_data = {'goodreads_id': goodreads_id}
    url = f'https://www.goodreads.com/book/show/{goodreads_id}'
    print(f"Scraping metadata from URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # --- Title & Author
        book_title_elem = soup.find('h1', class_='Text__title1')
        book_data['title'] = book_title_elem.text.strip() if book_title_elem else None

        author_elem = soup.find('span', class_='ContributorLink__name')
        if author_elem:
            book_data['author'] = author_elem.get_text(strip=True)
        else:
            author_elem = soup.find('span', class_='Text__title3')
            if author_elem:
                author_link = author_elem.find('a')
                book_data['author'] = author_link.get_text(strip=True) if author_link else None
            else:
                book_data['author'] = None

        # --- Average Rating
        rating_elem = soup.find('div', class_='RatingStatistics__rating')
        if rating_elem:
            try:
                book_data['average_rating'] = Decimal(rating_elem.text.strip())
            except (ValueError, InvalidOperation):
                book_data['average_rating'] = None

        # --- Num Ratings and Num Reviews (Meta Section; uses data-testid attrs for robustness!)
        stats_container = soup.find('div', class_='RatingStatistics__meta')
        if stats_container:
            # Ratings
            ratings_span = stats_container.find('span', {'data-testid': 'ratingsCount'})
            if ratings_span:
                ratings_match = re.search(r'([\d,]+)', ratings_span.text)
                if ratings_match:
                    book_data['num_ratings'] = int(ratings_match.group(1).replace(",", ""))
                else:
                    book_data['num_ratings'] = None
            # Reviews
            reviews_span = stats_container.find('span', {'data-testid': 'reviewsCount'})
            if reviews_span:
                reviews_match = re.search(r'([\d,]+)', reviews_span.text)
                if reviews_match:
                    book_data['num_reviews'] = int(reviews_match.group(1).replace(",", ""))
                else:
                    book_data['num_reviews'] = None

        # --- Cover
        cover_elem = soup.find('img', class_='ResponsiveImage')
        book_data['cover_image_url'] = cover_elem['src'] if cover_elem else None

        # --- Description
        description_elem = soup.find('div', {'data-testid': 'description'})
        if description_elem:
            book_data['description'] = description_elem.text.strip()

        return book_data

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] HTTP request failed for Goodreads metadata: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during Goodreads metadata scrape: {e}")
        return None


def get_goodreads_reviews(goodreads_id, max_reviews_to_scrape=50):
    """
    Scrape Goodreads reviews across all paginated batches (button click replaces page),
    extracting new reviews after each load and deduplicating by (reviewer, date, text[:100]).
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    reviews_data = []
    seen_dedupes = set()

    options = Options()
    # options.add_argument("--headless")  # Uncomment for headless mode
    driver = webdriver.Chrome(options=options)
    try:
        reviews_page_url = f'https://www.goodreads.com/book/show/{goodreads_id}/reviews'
        driver.get(reviews_page_url)
        
        wait = WebDriverWait(driver, 10)

        batch_num = 0
        scraped_total = 0
        while True:
            # Wait for review cards to load
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'ReviewCard')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            review_containers = soup.find_all('article', class_='ReviewCard')
            
            batch_count = 0
            for container in review_containers:
                # --- Extract review text
                review_text = ''
                review_text_element = container.find('div', {'data-testid': 'contentContainer'})
                if review_text_element:
                    review_text = review_text_element.get_text(strip=True)
                
                # --- Extract reviewer name
                reviewer_name = 'Unknown'
                name_div = container.find('div', {'data-testid': 'name'})
                if name_div:
                    name_link = name_div.find('a')
                    if name_link:
                        reviewer_name = name_link.get_text(strip=True)
                
                # --- Extract rating
                rating = None
                rating_element = container.find('span', class_='RatingStars')
                if rating_element:
                    rating_label = rating_element.get('aria-label')
                    if rating_label and 'Rating' in rating_label:
                        rating_value_match = re.search(r'Rating\s*([\d.]+)\s*out\s*of\s*5', rating_label)
                        if rating_value_match:
                            rating = Decimal(rating_value_match.group(1))

                # --- Extract date (using correct selector structure)
                review_date = None
                date_span = container.find('span', class_='Text Text__body3')
                if date_span:
                    a_tag = date_span.find('a')
                    if a_tag:
                        review_date_str = a_tag.get_text(strip=True)
                        try:
                            review_date = datetime.strptime(review_date_str, '%B %d, %Y')
                        except Exception:
                            pass

                # --- Robust deduplication key: reviewer, date, first 100 chars of text
                trunc_txt = (review_text or '')[:100]
                dedup_key = (reviewer_name or "Unknown", review_date or "", trunc_txt)
                if dedup_key in seen_dedupes:
                    continue
                seen_dedupes.add(dedup_key)

                reviews_data.append({
                    'review_text': review_text,
                    'review_date': review_date,
                    'reviewer_name': reviewer_name,
                    'rating': rating
                })
                batch_count += 1
                scraped_total += 1
                if max_reviews_to_scrape != -1 and scraped_total >= max_reviews_to_scrape:
                    print(f"Collected {scraped_total} reviews (limit reached).")
                    return reviews_data
            
            print(f"Batch {batch_num + 1}: Scraped {batch_count} reviews, {scraped_total} total.")
            batch_num += 1

            # Try to click "Show more reviews" for next batch
            try:
                load_more_button = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-testid='loadMore']"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(2)  # Wait for DOM update
            except (NoSuchElementException, TimeoutException):
                print("No more 'Show more reviews' button; finished scraping all batches.")
                break
            except ElementClickInterceptedException:
                time.sleep(2)
                continue  # Try again

        print(f"Total reviews scraped across batches: {len(reviews_data)}")
        return reviews_data

    finally:
        driver.quit()

def save_goodreads_reviews_to_db(book, reviews_data):
    print(f"DEBUG: Processing {len(reviews_data)} reviews for book '{book.title}'")
    
    reviews_to_create = []
    
    for review_data in reviews_data:
        # Check if a review with the same reviewer and date already exists for this book
        if review_data.get('reviewer_name') and review_data.get('review_date'):
            existing_review = Review.objects.filter(
                book=book,
                reviewer_name=review_data['reviewer_name'],
                review_date=review_data['review_date']
            ).first()

            if existing_review:
                print(f"INFO: Skipping duplicate review by '{review_data['reviewer_name']}' on {review_data['review_date']}.")
                continue
        
        # If no duplicate is found, prepare the review for saving
        rating_value = review_data.get('rating')
        if rating_value is not None:
            try:
                rating_decimal = Decimal(str(rating_value))
            except InvalidOperation:
                rating_decimal = None
        else:
            rating_decimal = None

        sentiment_score = 0
        sentiment_label = 'Neutral'
        if review_data['review_text']:
            sentiment_score = sid.polarity_scores(review_data['review_text'])['compound']
            if sentiment_score >= 0.05:
                sentiment_label = 'Positive'
            elif sentiment_score <= -0.05:
                sentiment_label = 'Negative'
            else:
                sentiment_label = 'Neutral'

        reviews_to_create.append(Review(
            book=book,
            review_text=review_data['review_text'],
            review_date=review_data.get('review_date'),
            reviewer_name=review_data['reviewer_name'],
            rating=rating_decimal,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label
        ))

    try:
        with transaction.atomic():
            if reviews_to_create:
                Review.objects.bulk_create(reviews_to_create)
                print(f"DEBUG: Successfully saved {len(reviews_to_create)} new reviews to the database.")
            else:
                print("DEBUG: No new reviews to save.")
    except Exception as e:
        print(f"ERROR: Failed to save reviews to the database. Reason: {e}")