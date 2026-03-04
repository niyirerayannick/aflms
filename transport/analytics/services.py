from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from transport.maintenance.models import MaintenanceRecord
from transport.trips.models import Trip
from transport.vehicles.models import Vehicle


def executive_dashboard_metrics():
    now = timezone.now()
    month_start = now.date().replace(day=1)

    active_trips = Trip.objects.filter(status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT]).count()
    available_vehicles = Vehicle.objects.filter(status=Vehicle.VehicleStatus.AVAILABLE).count()
    vehicles_in_maintenance = Vehicle.objects.filter(status=Vehicle.VehicleStatus.MAINTENANCE).count()

    monthly_trip_totals = Trip.objects.filter(created_at__date__gte=month_start).aggregate(
        monthly_revenue=Sum("revenue"),
        monthly_fuel_cost=Sum("fuel_cost"),
        monthly_maintenance_proxy=Sum("other_expenses"),
        net_profit=Sum("profit"),
    )
    monthly_maintenance_cost = (
        MaintenanceRecord.objects.filter(service_date__gte=month_start)
        .aggregate(total=Sum("cost"))
        .get("total")
        or Decimal("0")
    )

    fleet_total = Vehicle.objects.count() or 1
    busy_vehicles = Vehicle.objects.filter(status=Vehicle.VehicleStatus.ASSIGNED).count()
    fleet_utilization = round((busy_vehicles / fleet_total) * 100, 2)

    return {
        "active_trips": active_trips,
        "available_vehicles": available_vehicles,
        "vehicles_in_maintenance": vehicles_in_maintenance,
        "monthly_revenue": monthly_trip_totals.get("monthly_revenue") or Decimal("0"),
        "monthly_fuel_cost": monthly_trip_totals.get("monthly_fuel_cost") or Decimal("0"),
        "monthly_maintenance_cost": monthly_maintenance_cost,
        "net_profit": monthly_trip_totals.get("net_profit") or Decimal("0"),
        "fleet_utilization_percent": fleet_utilization,
    }
