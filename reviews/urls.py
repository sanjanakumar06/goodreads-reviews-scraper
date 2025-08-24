# In reviews/urls.py

from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # The home page 
    path('', views.book_list, name='book_list'),
    
    # Detail page for a specific book
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    
    # The page to trigger the scraping action
    path('scrape/', views.scrape_book, name='scrape_book'),
]