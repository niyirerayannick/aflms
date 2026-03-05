from django.urls import include, path

# Transport Management System URL Configuration
# Provides a clean API structure for all transport modules

app_name = 'transport'

urlpatterns = [
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