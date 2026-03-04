from django.contrib import admin

from .models import FuelEntry


@admin.register(FuelEntry)
class FuelEntryAdmin(admin.ModelAdmin):
    list_display = ("trip", "date", "liters", "price_per_liter", "total_cost", "fuel_station")
    list_filter = ("date", "fuel_station")
    search_fields = ("trip__order_number", "trip__vehicle__plate_number", "fuel_station")
    autocomplete_fields = ("trip",)
