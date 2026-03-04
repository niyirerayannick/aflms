from django.db import models

from transport.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    name = models.CharField(max_length=255, db_index=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("manage_customers", "Can manage customers"),
        ]

    def __str__(self):
        return self.name
