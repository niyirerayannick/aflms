from django.contrib import admin

from .models import FuelRequest, FuelStation


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ("name", "location")
    search_fields = ("name", "location")


@admin.register(FuelRequest)
class FuelRequestAdmin(admin.ModelAdmin):
    list_display = ("trip", "driver", "station", "amount", "is_approved", "created_at")
    list_filter = ("is_approved", "station")
    search_fields = ("trip__order_number", "driver__username", "station__name")
    autocomplete_fields = ("trip", "driver", "station")
