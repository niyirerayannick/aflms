from django.db import models
from django.db.models import Sum
from django.utils import timezone

from .models import MaintenanceRecord


def near_service_alerts(buffer_km=500):
    from transport.vehicles.models import Vehicle

    return Vehicle.objects.filter(current_odometer__gte=models.F("next_service_km") - buffer_km).order_by("plate_number")


def monthly_maintenance_cost(month_start, month_end):
    return (
        MaintenanceRecord.objects.filter(service_date__gte=month_start, service_date__lte=month_end)
        .aggregate(total=Sum("cost"))
        .get("total")
        or 0
    )


def total_downtime_days(month_start, month_end):
    return (
        MaintenanceRecord.objects.filter(service_date__gte=month_start, service_date__lte=month_end)
        .aggregate(total=Sum("downtime_days"))
        .get("total")
        or 0
    )
