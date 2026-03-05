from django.contrib import admin

from .models import FuelEntry, FuelStation


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "contact_person", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "location", "contact_person")
    list_editable = ("is_active",)


@admin.register(FuelEntry)
class FuelEntryAdmin(admin.ModelAdmin):
    list_display = ("trip", "date", "liters", "price_per_liter", "total_cost", "station", "fuel_station")
    list_filter = ("date", "station")
    search_fields = ("trip__order_number", "trip__vehicle__plate_number", "fuel_station", "station__name")
    autocomplete_fields = ("trip", "station")
