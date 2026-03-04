from decimal import Decimal

from django.db import models

from transport.core.models import TimeStampedModel
from transport.vehicles.models import Vehicle


class MaintenanceRecord(TimeStampedModel):
    vehicle = models.ForeignKey("atms_vehicles.Vehicle", on_delete=models.CASCADE, related_name="maintenance_records")
    service_type = models.CharField(max_length=80)
    service_date = models.DateField()
    service_km = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    workshop = models.CharField(max_length=255)
    downtime_days = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-service_date"]
        indexes = [models.Index(fields=["vehicle", "service_date"])]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.service_type}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.service_km >= self.vehicle.last_service_km:
            self.vehicle.last_service_km = self.service_km
            self.vehicle.status = Vehicle.VehicleStatus.MAINTENANCE if self.downtime_days > 0 else Vehicle.VehicleStatus.AVAILABLE
            self.vehicle.save(update_fields=["last_service_km", "next_service_km", "status", "updated_at"])

    @property
    def maintenance_cost_per_km(self):
        if self.service_km <= 0:
            return Decimal("0")
        return self.cost / Decimal(self.service_km)
