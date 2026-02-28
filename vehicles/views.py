from django.http import JsonResponse

from .models import Vehicle


def vehicles_summary(_request):
    return JsonResponse(
        {
            "total_vehicles": Vehicle.objects.count(),
            "active_vehicles": Vehicle.objects.filter(status=Vehicle.Status.ACTIVE).count(),
        }
    )
