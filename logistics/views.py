from django.http import JsonResponse

from .models import ShipmentOrder


def logistics_summary(_request):
    return JsonResponse(
        {
            "total_orders": ShipmentOrder.objects.count(),
            "in_transit": ShipmentOrder.objects.filter(status=ShipmentOrder.Status.IN_TRANSIT).count(),
            "delivered": ShipmentOrder.objects.filter(status=ShipmentOrder.Status.DELIVERED).count(),
        }
    )
