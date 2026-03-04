from django.db import models
from django.utils import timezone

from transport.core.models import TimeStampedModel


class Driver(TimeStampedModel):
    class DriverStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        LEAVE = "LEAVE", "Leave"

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    license_number = models.CharField(max_length=80, unique=True)
    license_category = models.CharField(max_length=16)
    license_expiry = models.DateField()
    status = models.CharField(max_length=16, choices=DriverStatus.choices, default=DriverStatus.AVAILABLE)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "license_expiry"]),
            models.Index(fields=["license_number"]),
        ]
        permissions = [
            ("manage_drivers", "Can manage drivers"),
        ]

    def __str__(self):
        return self.name

    def can_be_assigned(self):
        if self.status != self.DriverStatus.AVAILABLE:
            return False, "Driver is not available."
        if self.license_expiry < timezone.now().date():
            return False, "Driver license is expired."
        return True, "OK"
