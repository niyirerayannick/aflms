from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate_number",
        "vehicle_type",
        "status",
        "current_odometer",
        "insurance_expiry",
        "inspection_expiry",
        "next_service_km",
    )
    list_filter = ("status", "vehicle_type")
    search_fields = ("plate_number", "vehicle_type")
