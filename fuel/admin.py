from django.contrib import admin

from .models import FuelLog


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "liters", "cost", "odometer_km", "fuel_date")
    list_filter = ("fuel_date", "vehicle")
    search_fields = ("vehicle__registration_number", "station_name")
