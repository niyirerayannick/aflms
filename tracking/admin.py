from django.contrib import admin

from .models import GPSLocation


@admin.register(GPSLocation)
class GPSLocationAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "driver", "latitude", "longitude", "speed_kmh", "recorded_at")
    list_filter = ("vehicle",)
    search_fields = ("vehicle__registration_number",)
