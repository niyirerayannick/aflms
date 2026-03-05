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
        .order_by("-created_at")
    )
