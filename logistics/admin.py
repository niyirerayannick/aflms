from django.contrib import admin

from .models import ShipmentOrder


@admin.register(ShipmentOrder)
class ShipmentOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "client", "vehicle", "driver", "status", "expected_delivery_date")
    list_filter = ("status", "expected_delivery_date")
    search_fields = ("order_number", "client__name", "commodity_name", "origin", "destination")
