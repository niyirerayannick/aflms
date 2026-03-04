from django.db.models import Sum
from django.db.models.functions import TruncMonth

from .models import FuelEntry


def fuel_efficiency_for_trip(trip):
    liters = trip.fuel_issued or 0
    distance = trip.distance or 0
    if liters <= 0:
        return 0
    return round(float(distance / liters), 2)


def monthly_fuel_by_vehicle(month_start, month_end):
    return (
        FuelEntry.objects.filter(date__gte=month_start, date__lte=month_end)
        .values("trip__vehicle__plate_number")
        .annotate(total_liters=Sum("liters"), total_cost=Sum("total_cost"))
        .order_by("trip__vehicle__plate_number")
    )


def fuel_cost_ratio(trip):
    if not trip.revenue:
        return 0
    return round(float(trip.fuel_cost / trip.revenue), 4)


def flagged_consumption(threshold_cost_ratio=0.45):
    flagged = []
    for row in FuelEntry.objects.select_related("trip").all():
        if row.trip.revenue and row.trip.fuel_cost / row.trip.revenue > threshold_cost_ratio:
            flagged.append(row)
    return flagged


def monthly_fuel_trend():
    return (
        FuelEntry.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_cost=Sum("total_cost"), total_liters=Sum("liters"))
        .order_by("month")
    )
