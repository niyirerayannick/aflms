from django.http import JsonResponse

from .models import GPSLocation


def tracking_summary(_request):
    latest = GPSLocation.objects.first()
    return JsonResponse(
        {
            "total_gps_points": GPSLocation.objects.count(),
            "latest_recorded_at": latest.recorded_at.isoformat() if latest else None,
        }
    )
