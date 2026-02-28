from django.conf import settings
from django.db import models

from vehicles.models import Vehicle


class DriverProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=80, unique=True)
    phone_number = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=120, blank=True)
    assigned_vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_drivers"
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
