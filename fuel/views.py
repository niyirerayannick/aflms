from django.db.models import Sum
from django.http import JsonResponse

from .models import FuelLog


def fuel_summary(_request):
    aggregate = FuelLog.objects.aggregate(total_liters=Sum("liters"), total_cost=Sum("cost"))
    return JsonResponse(
        {
            "entries": FuelLog.objects.count(),
            "total_liters": float(aggregate["total_liters"] or 0),
            "total_cost": float(aggregate["total_cost"] or 0),
        }
    )
