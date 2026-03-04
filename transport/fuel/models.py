from decimal import Decimal

from django.db import models

from transport.core.models import TimeStampedModel


class FuelEntry(TimeStampedModel):
    trip = models.ForeignKey("atms_trips.Trip", on_delete=models.CASCADE, related_name="fuel_entries")
    liters = models.DecimalField(max_digits=12, decimal_places=2)
    price_per_liter = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_station = models.CharField(max_length=255)
    date = models.DateField()

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["trip", "date"]),
            models.Index(fields=["fuel_station"]),
        ]

    def __str__(self):
        return f"{self.trip.order_number} - {self.liters} L"

    def save(self, *args, **kwargs):
        self.total_cost = (self.liters or Decimal("0")) * (self.price_per_liter or Decimal("0"))
        super().save(*args, **kwargs)
        self.trip.fuel_issued = sum(self.trip.fuel_entries.values_list("liters", flat=True), Decimal("0"))
        self.trip.fuel_cost = sum(self.trip.fuel_entries.values_list("total_cost", flat=True), Decimal("0"))
        self.trip.save(update_fields=["fuel_issued", "fuel_cost", "distance", "total_cost", "profit", "cost_per_km", "revenue_per_km", "updated_at"])
