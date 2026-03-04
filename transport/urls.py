from django.urls import include, path

# Transport Management System URL Configuration
# Provides a clean API structure for all transport modules

urlpatterns = [
    # Core analytics and dashboard
    path("analytics/", include("transport.analytics.urls", namespace="analytics")),
    
    # Core transport modules
    path("vehicles/", include("transport.vehicles.urls")),
    path("drivers/", include("transport.drivers.urls")),
    path("customers/", include("transport.customers.urls")),
    path("routes/", include("transport.routes.urls")),
    path("trips/", include("transport.trips.urls")),
    
    # Operations modules
    path("fuel/", include("transport.fuel.urls")),
    path("maintenance/", include("transport.maintenance.urls")),
    path("finance/", include("transport.finance.urls")),
    path("reports/", include("transport.reports.urls")),
]