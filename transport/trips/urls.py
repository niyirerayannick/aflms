from django.urls import path
from transport.analytics.views import TripListView, TripDetailView

# Trip management endpoints 
urlpatterns = [
    path("", TripListView.as_view(), name="transport-trips-list"),
    path("<int:pk>/", TripDetailView.as_view(), name="transport-trip-detail"),
    # Add more trip endpoints as needed
]