from django.urls import include, path
from . import views

# Transport Management System URL Configuration
# Provides a clean API structure for all transport modules

app_name = 'transport'

urlpatterns = [
    path("driver.webmanifest", views.driver_manifest, name="driver_manifest"),
    path("driver-sw.js", views.driver_service_worker, name="driver_service_worker"),
    path("driver/", views.driver_dashboard, name="driver_home"),
    path("driver/dashboard/", views.driver_dashboard, name="driver_dashboard"),
    path("driver/trips/", views.driver_trips, name="driver_trips"),
    path("driver/fuel/", views.driver_fuel, name="driver_fuel"),
    path("driver/profile/", views.driver_profile, name="driver_profile"),
    path("driver/partials/dashboard/", views.driver_dashboard_partial, name="driver_dashboard_partial"),
    path("driver/partials/trips/", views.driver_trips_partial, name="driver_trips_partial"),
    path("driver/partials/fuel/", views.driver_fuel_partial, name="driver_fuel_partial"),
    path("driver/partials/profile/", views.driver_profile_partial, name="driver_profile_partial"),
    path("driver/assignment-state/", views.driver_assignment_state, name="driver_assignment_state"),
    # Core analytics and dashboard
    path("analytics/", include("transport.analytics.urls", namespace="analytics")),
    
    # Core transport modules - only include working modules
    path("vehicles/", include("transport.vehicles.urls", namespace="vehicles")),
    
    # Enabled transport modules
    path("drivers/", include("transport.drivers.urls", namespace="drivers")),
    path("customers/", include("transport.customers.urls", namespace="customers")),
    path("routes/", include("transport.routes.urls", namespace="routes")),
    path("fuel/", include("transport.fuel.urls", namespace="fuel")),
    path("trips/", include("transport.trips.urls", namespace="trips")),
    path("maintenance/", include("transport.maintenance.urls", namespace="maintenance")),
    path("finance/", include("transport.finance.urls", namespace="finance")),
    
    # Reports module
    path("reports/", include("transport.reports.urls", namespace="reports")),
    
    # Messaging (WhatsApp integration)
    path("messaging/", include("transport.messaging.urls", namespace="messaging")),
]
