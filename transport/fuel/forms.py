from django import forms
from .models import FuelRequest, FuelDocument
from transport.trips.models import Trip
from transport.drivers.models import Driver

class FuelRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        driver_user = kwargs.pop("driver_user", None)
        super().__init__(*args, **kwargs)

        if driver_user is None:
            self.fields["trip"].queryset = Trip.objects.none()
            return

        driver = Driver.objects.filter(user=driver_user).first()
        if driver is None:
            self.fields["trip"].queryset = Trip.objects.none()
            return

        self.fields["trip"].queryset = Trip.objects.filter(
            driver=driver,
            status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT],
        ).order_by("-created_at")

    class Meta:
        model = FuelRequest
        fields = ['trip', 'station', 'amount', 'notes']

class FuelDocumentForm(forms.ModelForm):
    class Meta:
        model = FuelDocument
        fields = ['document']
