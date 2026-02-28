from django.http import JsonResponse

from .models import Notification


def notifications_summary(_request):
    return JsonResponse(
        {
            "total_notifications": Notification.objects.count(),
            "unread_notifications": Notification.objects.exclude(status=Notification.Status.READ).count(),
        }
    )
