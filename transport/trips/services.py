from django.db.models import Prefetch

from .models import Trip


def trip_queryset_for_operations():
    return (
        Trip.objects.select_related(
            "customer",
            "commodity_type",
            "route",
            "vehicle",
            "driver",
        )
        .prefetch_related(Prefetch("fuel_entries"), Prefetch("payments"))
        .order_by("-created_at")
    )
