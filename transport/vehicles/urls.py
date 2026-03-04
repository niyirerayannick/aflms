from django.urls import path
from transport.analytics.views import VehicleListView

# Vehicle management endpoints
urlpatterns = [
    path("", VehicleListView.as_view(), name="transport-vehicles-list"),
    # path("<int:pk>/", VehicleDetailView.as_view(), name="transport-vehicle-detail"),
    # Add more vehicle endpoints as needed
]