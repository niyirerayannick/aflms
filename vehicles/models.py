from django.db import models


class Vehicle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        INACTIVE = "inactive", "Inactive"

    registration_number = models.CharField(max_length=30, unique=True)
    vin = models.CharField(max_length=50, unique=True)
    make = models.CharField(max_length=120)
    model = models.CharField(max_length=120)
    year = models.PositiveIntegerField()
    capacity_tons = models.DecimalField(max_digits=7, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"
