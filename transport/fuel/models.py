from decimal import Decimal

from django.db import models

from transport.core.models import TimeStampedModel


class FuelStation(TimeStampedModel):
    """Fuel stations that work with us."""
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        if self.location:
            return f"{self.name} — {self.location}"
        return self.name


class FuelEntry(TimeStampedModel):
    trip = models.ForeignKey("atms_trips.Trip", on_delete=models.CASCADE, related_name="fuel_entries")
    liters = models.DecimalField(max_digits=12, decimal_places=2)
    price_per_liter = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    station = models.ForeignKey(
        FuelStation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fuel_entries",
    )
    fuel_station = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    invoice = models.FileField(upload_to="fuel/invoices/%Y/%m/", blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["trip", "date"]),
            models.Index(fields=["station"]),
        ]

    def __str__(self):
        return f"{self.trip.order_number} - {self.liters} L"

    def save(self, *args, **kwargs):
        self.total_cost = (self.liters or Decimal("0")) * (self.price_per_liter or Decimal("0"))
        # Keep legacy fuel_station text in sync with FK
        if self.station_id and not self.fuel_station:
            self.fuel_station = self.station.name
        super().save(*args, **kwargs)
        self.trip.fuel_issued = sum(self.trip.fuel_entries.values_list("liters", flat=True), Decimal("0"))
        self.trip.fuel_cost = sum(self.trip.fuel_entries.values_list("total_cost", flat=True), Decimal("0"))
        self.trip.save(update_fields=["fuel_issued", "fuel_cost", "distance", "total_cost", "profit", "cost_per_km", "revenue_per_km", "updated_at"])
