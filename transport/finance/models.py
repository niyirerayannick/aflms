from django.db import models

from transport.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    trip = models.ForeignKey("atms_trips.Trip", on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        indexes = [models.Index(fields=["trip", "payment_date"])]

    def __str__(self):
        return f"{self.trip.order_number} - {self.amount}"


class Expense(TimeStampedModel):
    trip = models.ForeignKey("atms_trips.Trip", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    category = models.CharField(max_length=80)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        indexes = [models.Index(fields=["expense_date", "category"])]

    def __str__(self):
        return f"{self.category} - {self.amount}"
