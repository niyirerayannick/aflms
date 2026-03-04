from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "route",
        "vehicle",
        "driver",
        "status",
        "distance",
        "revenue",
        "profit",
    )
    list_filter = ("status", "commodity_type")
    search_fields = ("order_number", "customer__name", "vehicle__plate_number", "driver__name")
    autocomplete_fields = ("customer", "commodity_type", "route", "vehicle", "driver")
