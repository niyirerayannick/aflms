from django.urls import path

from .views import (
    dashboard_view, 
    dashboard_api,
    VehicleListView,
    TripListView, 
    TripDetailView,
    driver_dashboard,
    client_dashboard,
    executive_dashboard_api  # Legacy endpoint
)

app_name = "analytics"

urlpatterns = [
    # Main dashboards
    path("dashboard/", dashboard_view, name="dashboard"),
    path("api/dashboard/", dashboard_api, name="dashboard-api"),
    path("driver-dashboard/", driver_dashboard, name="driver-dashboard"),
    path("client-dashboard/", client_dashboard, name="client-dashboard"),
    
    # Management views
    path("vehicles/", VehicleListView.as_view(), name="vehicles-list"),
    path("trips/", TripListView.as_view(), name="trips-list"),
    path("trips/<int:pk>/", TripDetailView.as_view(), name="trip-detail"),
    
    # Legacy API endpoint
    path("executive/", executive_dashboard_api, name="atms-executive-dashboard"),
]
