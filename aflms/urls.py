from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(_request):
    return JsonResponse({"status": "ok", "service": "aflms"})


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("", include("allauth.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/vehicles/", include("vehicles.urls")),
    path("api/drivers/", include("drivers.urls")),
    path("api/tracking/", include("tracking.urls")),
    path("api/fuel/", include("fuel.urls")),
    path("api/clients/", include("clients.urls")),
    path("api/logistics/", include("logistics.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/notifications/", include("notifications.urls")),
]
