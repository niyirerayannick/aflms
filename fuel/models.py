from django.db import models

from vehicles.models import Vehicle


class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="fuel_logs")
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    odometer_km = models.PositiveIntegerField()
    station_name = models.CharField(max_length=150, blank=True)
    fuel_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fuel_date"]

    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.liters}L"
