from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from transport.core.models import TimeStampedModel


class Vehicle(TimeStampedModel):
    class VehicleStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        MAINTENANCE = "MAINTENANCE", "Maintenance"

    class VehicleType(models.TextChoices):
        TRUCK = "TRUCK", "Truck"
        TANKER = "TANKER", "Tanker"
        TRAILER = "TRAILER", "Trailer"
        PICKUP = "PICKUP", "Pickup"
        VAN = "VAN", "Van"
        FLATBED = "FLATBED", "Flatbed"

    # Backward compatibility property
    STATUS_CHOICES = VehicleStatus.choices
    VEHICLE_TYPE_CHOICES = VehicleType.choices

    plate_number = models.CharField(max_length=40, unique=True)
    vehicle_type = models.CharField(max_length=60, choices=VehicleType.choices, default=VehicleType.TRUCK)
    capacity = models.DecimalField(max_digits=12, decimal_places=2)
    current_odometer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=16, choices=VehicleStatus.choices, default=VehicleStatus.AVAILABLE)
    insurance_expiry = models.DateField()
    inspection_expiry = models.DateField()
    service_interval_km = models.PositiveIntegerField(default=10000)
    last_service_km = models.PositiveIntegerField(default=0)
    next_service_km = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["plate_number"]
        indexes = [
            models.Index(fields=["status", "insurance_expiry"]),
            models.Index(fields=["inspection_expiry"]),
        ]
        permissions = [
            ("manage_vehicles", "Can manage vehicles"),
        ]

    def __str__(self):
        return self.plate_number

    def clean(self):
        if self.service_interval_km <= 0:
            raise ValidationError({"service_interval_km": "Service interval must be greater than zero."})
        if self.current_odometer < 0:
            raise ValidationError({"current_odometer": "Current odometer cannot be negative."})

    def calculate_next_service_km(self):
        return int(self.last_service_km + self.service_interval_km)

    def can_be_assigned(self):
        today = timezone.now().date()
        if self.status != self.VehicleStatus.AVAILABLE:
            return False, "Vehicle is not available."
        if self.insurance_expiry < today:
            return False, "Vehicle insurance is expired."
        if self.inspection_expiry < today:
            return False, "Vehicle inspection is expired."
        return True, "OK"

    def save(self, *args, **kwargs):
        self.next_service_km = self.calculate_next_service_km()
        super().save(*args, **kwargs)
