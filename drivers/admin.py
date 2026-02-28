from django.contrib import admin

from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "license_number", "assigned_vehicle", "is_available")
    list_filter = ("is_available",)
    search_fields = ("user__username", "license_number", "phone_number")
