import json
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from transport.customers.models import Customer
from transport.drivers.models import Driver
from transport.finance.models import Expense, Payment
from transport.fuel.models import FuelRequest, FuelStation
from transport.maintenance.models import MaintenanceRecord
from transport.routes.models import Route
from transport.trips.models import Trip
from transport.vehicles.models import Vehicle


def executive_dashboard_metrics():
    """Core KPI cards."""
    now = timezone.now()
    month_start = now.date().replace(day=1)

    active_trips = Trip.objects.filter(
        status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT]
    ).count()
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


def full_dashboard_context():
    """Return everything needed for the comprehensive dashboard template."""
    now = timezone.now()
    today = now.date()
    month_start = today.replace(day=1)
    twelve_months_ago = (today - timedelta(days=365)).replace(day=1)

    # ── 1. Core KPIs ──────────────────────────────────────────────────
    metrics = executive_dashboard_metrics()

    # ── 2. Entity totals ──────────────────────────────────────────────
    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()
    total_customers = Customer.objects.count()
    total_routes = Route.objects.count()
    total_trips = Trip.objects.count()
    total_fuel_stations = FuelStation.objects.count()

    # ── 3. Fleet breakdown ────────────────────────────────────────────
    fleet_by_status = dict(
        Vehicle.objects.values_list("status").annotate(c=Count("id")).values_list("status", "c")
    )
    fleet_by_type = list(
        Vehicle.objects.values("vehicle_type").annotate(count=Count("id")).order_by("-count")
    )

    # ── 4. Driver breakdown ───────────────────────────────────────────
    driver_by_status = dict(
        Driver.objects.values_list("status").annotate(c=Count("id")).values_list("status", "c")
    )

    # ── 5. Trip breakdown ─────────────────────────────────────────────
    trip_by_status = list(
        Trip.objects.values("status").annotate(count=Count("id")).order_by("status")
    )
    monthly_trips = Trip.objects.filter(created_at__date__gte=month_start).count()
    delivered_trips = Trip.objects.filter(status=Trip.TripStatus.DELIVERED).count()
    closed_trips = Trip.objects.filter(status=Trip.TripStatus.CLOSED).count()

    # ── 6. Financial all-time aggregates ──────────────────────────────
    fin = Trip.objects.aggregate(
        all_revenue=Sum("revenue"),
        all_cost=Sum("total_cost"),
        all_profit=Sum("profit"),
        all_fuel_cost=Sum("fuel_cost"),
        all_distance=Sum("distance"),
    )
    total_revenue = fin["all_revenue"] or Decimal("0")
    total_cost = fin["all_cost"] or Decimal("0")
    total_profit = fin["all_profit"] or Decimal("0")
    total_fuel_cost = fin["all_fuel_cost"] or Decimal("0")
    total_distance = fin["all_distance"] or Decimal("0")
    total_payments = Payment.objects.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    total_expenses = Expense.objects.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    total_maintenance_cost = MaintenanceRecord.objects.aggregate(s=Sum("cost"))["s"] or Decimal("0")

    # ── 7. Revenue / profit trend (12 months) ─────────────────────────
    monthly_trend = list(
        Trip.objects.filter(created_at__date__gte=twelve_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            revenue=Sum("revenue"),
            cost=Sum("total_cost"),
            profit=Sum("profit"),
            count=Count("id"),
        )
        .order_by("month")
    )
    trend_labels = json.dumps([m["month"].strftime("%b %Y") for m in monthly_trend])
    trend_revenue = json.dumps([float(m["revenue"] or 0) for m in monthly_trend])
    trend_cost = json.dumps([float(m["cost"] or 0) for m in monthly_trend])
    trend_profit = json.dumps([float(m["profit"] or 0) for m in monthly_trend])
    trend_count = json.dumps([m["count"] for m in monthly_trend])

    # ── 8. Fuel trend (12 months) ─────────────────────────────────────


    # ── 9. Trip status pie chart ──────────────────────────────────────
    status_labels = json.dumps([s["status"] for s in trip_by_status])
    status_counts = json.dumps([s["count"] for s in trip_by_status])

    # ── 10. Vehicle type pie chart ────────────────────────────────────
    vtype_labels = json.dumps([v["vehicle_type"] or "Unknown" for v in fleet_by_type])
    vtype_counts = json.dumps([v["count"] for v in fleet_by_type])

    # ── 11. Top customers by revenue ──────────────────────────────────
    top_customers = list(
        Trip.objects.values("customer__company_name")
        .annotate(revenue=Sum("revenue"), trips=Count("id"))
        .order_by("-revenue")[:5]
    )

    # ── 12. Top routes by trips ───────────────────────────────────────
    top_routes = list(
        Trip.objects.values("route__origin", "route__destination")
        .annotate(trips=Count("id"), revenue=Sum("revenue"))
        .order_by("-trips")[:5]
    )



    # ── 14. Alerts ────────────────────────────────────────────────────
    alerts = []

    # Vehicles in maintenance
    maint_vehicles = Vehicle.objects.filter(status=Vehicle.VehicleStatus.MAINTENANCE)
    for v in maint_vehicles[:5]:
        alerts.append({"type": "warning", "icon": "wrench", "message": f"{v.plate_number} is in maintenance", "link": f"/transport/vehicles/{v.pk}/"})

    # Insurance / inspection expiring within 30 days
    expires_soon = today + timedelta(days=30)
    insurance_exp = Vehicle.objects.filter(insurance_expiry__lte=expires_soon, insurance_expiry__gte=today)
    for v in insurance_exp[:5]:
        alerts.append({"type": "danger", "icon": "shield", "message": f"{v.plate_number} insurance expires {v.insurance_expiry.strftime('%d %b %Y')}", "link": f"/transport/vehicles/{v.pk}/"})

    inspection_exp = Vehicle.objects.filter(inspection_expiry__lte=expires_soon, inspection_expiry__gte=today)
    for v in inspection_exp[:5]:
        alerts.append({"type": "danger", "icon": "clipboard", "message": f"{v.plate_number} inspection expires {v.inspection_expiry.strftime('%d %b %Y')}", "link": f"/transport/vehicles/{v.pk}/"})

    # Drivers with license expiring in 30 days
    license_exp = Driver.objects.filter(license_expiry__lte=expires_soon, license_expiry__gte=today)
    for d in license_exp[:5]:
        alerts.append({"type": "danger", "icon": "id-card", "message": f"Driver {d} license expires {d.license_expiry.strftime('%d %b %Y')}", "link": f"/transport/drivers/{d.pk}/"})

    # Overdue trips (IN_TRANSIT for more than 7 days)
    overdue_cutoff = now - timedelta(days=7)
    overdue_trips = Trip.objects.filter(status=Trip.TripStatus.IN_TRANSIT, updated_at__lte=overdue_cutoff)
    for t in overdue_trips[:5]:
        alerts.append({"type": "warning", "icon": "clock", "message": f"Trip {t.order_number} in transit over 7 days", "link": f"/transport/trips/{t.pk}/"})

    # ── 15. Recent activity ───────────────────────────────────────────
    recent_trips = Trip.objects.select_related("customer", "vehicle", "driver", "route").order_by("-created_at")[:10]
    recent_maintenance = MaintenanceRecord.objects.select_related("vehicle").order_by("-service_date")[:5]
    recent_fuel = FuelRequest.objects.select_related("trip", "station").order_by("-created_at")[:5]
    recent_payments = Payment.objects.select_related("trip").order_by("-payment_date")[:5]

    # ── 16. Driver Leaderboard ────────────────────────────────────────
    top_drivers = list(
        Driver.objects.select_related("user")
        .annotate(trips_count=Count("trips", filter=Q(trips__status=Trip.TripStatus.DELIVERED)))
        .order_by("-trips_count")[:5]
    )

    return {
        "top_drivers": top_drivers,
        # Core KPIs
        "metrics": metrics,
        # Entity totals
        "total_vehicles": total_vehicles,
        "total_drivers": total_drivers,
        "total_customers": total_customers,
        "total_routes": total_routes,
        "total_trips": total_trips,
        "total_fuel_stations": total_fuel_stations,
        # Fleet
        "fleet_available": fleet_by_status.get("AVAILABLE", 0),
        "fleet_assigned": fleet_by_status.get("ASSIGNED", 0),
        "fleet_maintenance": fleet_by_status.get("MAINTENANCE", 0),
        "fleet_by_type": fleet_by_type,
        # Drivers
        "drivers_available": driver_by_status.get("AVAILABLE", 0),
        "drivers_assigned": driver_by_status.get("ASSIGNED", 0),
        "drivers_on_leave": driver_by_status.get("LEAVE", 0),
        # Trips
        "trip_by_status": trip_by_status,
        "monthly_trips": monthly_trips,
        "delivered_trips": delivered_trips,
        "closed_trips": closed_trips,
        # Financials
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_fuel_cost": total_fuel_cost,
        "total_distance": total_distance,
        "total_payments": total_payments,
        "total_expenses": total_expenses,
        "total_maintenance_cost": total_maintenance_cost,
        # Charts – Revenue trend
        "trend_labels": trend_labels,
        "trend_revenue": trend_revenue,
        "trend_cost": trend_cost,
        "trend_profit": trend_profit,
        "trend_count": trend_count,
        # Charts – Fuel trend

        # Charts – Trip status pie
        "status_labels": status_labels,
        "status_counts": status_counts,
        # Charts – Vehicle type pie
        "vtype_labels": vtype_labels,
        "vtype_counts": vtype_counts,
        # Rankings
        "top_customers": top_customers,
        "top_routes": top_routes,

        # Rankings

        # Alerts
        "alerts": alerts,
        "alert_count": len(alerts),
        # Recent activity
        "recent_trips": recent_trips,
        "recent_maintenance": recent_maintenance,
        "recent_fuel": recent_fuel,
        "recent_payments": recent_payments,
    }
