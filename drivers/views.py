from django.http import JsonResponse

from .models import DriverProfile


def drivers_summary(_request):
    return JsonResponse(
        {
            "total_drivers": DriverProfile.objects.count(),
            "available_drivers": DriverProfile.objects.filter(is_available=True).count(),
        }
    )
