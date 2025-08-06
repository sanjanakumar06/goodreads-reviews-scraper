from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # CORRECTED LINE: Added namespace='reviews'
    path('reviews/', include('reviews.urls', namespace='reviews')),
]