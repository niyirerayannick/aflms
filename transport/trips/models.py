from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from transport.core.models import TimeStampedModel


class Trip(TimeStampedModel):
    class TripStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        DELIVERED = "DELIVERED", "Delivered"
        CLOSED = "CLOSED", "Closed"

    order_number = models.CharField(max_length=40, unique=True, blank=True)
    customer = models.ForeignKey("atms_customers.Customer", on_delete=models.PROTECT, related_name="trips")
    commodity_type = models.ForeignKey("atms_core.CommodityType", on_delete=models.PROTECT, related_name="trips")
    route = models.ForeignKey("atms_routes.Route", on_delete=models.PROTECT, related_name="trips")
    vehicle = models.ForeignKey("atms_vehicles.Vehicle", on_delete=models.PROTECT, related_name="trips")
    driver = models.ForeignKey("atms_drivers.Driver", on_delete=models.PROTECT, related_name="trips")

    km_start = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    km_end = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    fuel_issued = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    distance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_per_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revenue_per_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=16, choices=TripStatus.choices, default=TripStatus.DRAFT)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["customer", "route"]),
            models.Index(fields=["vehicle", "driver"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=Q(status__in=["ASSIGNED", "IN_TRANSIT"]),
                name="atms_unique_active_vehicle_trip",
            ),
            models.UniqueConstraint(
                fields=["driver"],
                condition=Q(status__in=["ASSIGNED", "IN_TRANSIT"]),
                name="atms_unique_active_driver_trip",
            ),
        ]
        permissions = [
            ("approve_trip", "Can approve trip"),
            ("close_trip", "Can close trip"),
        ]

    def __str__(self):
        return self.order_number or f"Trip {self.pk}"

    def clean(self):
        if self.km_end and self.km_end < self.km_start:
            raise ValidationError({"km_end": "km_end cannot be less than km_start."})

        can_vehicle_assign, vehicle_reason = self.vehicle.can_be_assigned()
        can_driver_assign, driver_reason = self.driver.can_be_assigned()

        if self.status in {self.TripStatus.ASSIGNED, self.TripStatus.IN_TRANSIT}:
            if not can_vehicle_assign and self.vehicle.status != self.vehicle.VehicleStatus.ASSIGNED:
                raise ValidationError({"vehicle": vehicle_reason})
            if not can_driver_assign and self.driver.status != self.driver.DriverStatus.ASSIGNED:
                raise ValidationError({"driver": driver_reason})

    def calculate_distance(self):
        if self.km_end <= self.km_start:
            return Decimal("0")
        return self.km_end - self.km_start

    def recalculate_financials(self):
        self.distance = self.calculate_distance()
        self.total_cost = (self.fuel_cost or Decimal("0")) + (self.other_expenses or Decimal("0"))
        self.profit = (self.revenue or Decimal("0")) - self.total_cost
        if self.distance > 0:
            self.cost_per_km = self.total_cost / self.distance
            self.revenue_per_km = (self.revenue or Decimal("0")) / self.distance
        else:
            self.cost_per_km = Decimal("0")
            self.revenue_per_km = Decimal("0")

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_prefix = timezone.now().strftime("%Y%m%d")
            seed = Trip.objects.filter(order_number__startswith=f"ATMS-{date_prefix}").count() + 1
            self.order_number = f"ATMS-{date_prefix}-{seed:04d}"
        self.recalculate_financials()
        super().save(*args, **kwargs)
