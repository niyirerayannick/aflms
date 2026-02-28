from django.http import JsonResponse

from .models import ClientProfile


def clients_summary(_request):
    return JsonResponse(
        {
            "total_clients": ClientProfile.objects.count(),
            "active_clients": ClientProfile.objects.filter(is_active=True).count(),
        }
    )
