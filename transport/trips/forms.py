from django import forms
from django.db import models as db_models
from django.core.exceptions import ValidationError

from .models import Trip
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver
from transport.customers.models import Customer
from transport.routes.models import Route
from transport.core.models import CommodityType


INPUT_CSS = (
    "mt-1 block w-full rounded-md border-gray-300 shadow-sm "
    "focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
)


class TripForm(forms.ModelForm):
    """Form for creating and updating trips with comprehensive validation"""

    class Meta:
        model = Trip
        fields = [
            'customer', 'commodity_type', 'route', 'vehicle', 'driver',
            'quantity',
            'km_start', 'km_end', 'fuel_issued', 'fuel_cost',
            'other_expenses', 'revenue', 'status',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': INPUT_CSS, 'required': True}),
            'commodity_type': forms.Select(attrs={'class': INPUT_CSS, 'required': True}),
            'route': forms.Select(attrs={'class': INPUT_CSS, 'required': True}),
            'vehicle': forms.Select(attrs={'class': INPUT_CSS, 'required': True}),
            'driver': forms.Select(attrs={'class': INPUT_CSS, 'required': True}),
            'quantity': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
                'id': 'id_quantity',
            }),
            'km_start': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'km_end': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'fuel_issued': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'fuel_cost': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'other_expenses': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'revenue': forms.NumberInput(attrs={
                'class': INPUT_CSS, 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
            'status': forms.Select(attrs={'class': INPUT_CSS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter querysets
        self.fields['customer'].queryset = Customer.objects.filter(status=Customer.CustomerStatus.ACTIVE)
        self.fields['commodity_type'].queryset = CommodityType.objects.filter(is_active=True)
        self.fields['route'].queryset = Route.objects.filter(is_active=True)

        # For vehicles/drivers: if editing, include the already-assigned resources
        if self.instance and self.instance.pk:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(
                db_models.Q(status=Vehicle.VehicleStatus.AVAILABLE) |
                db_models.Q(pk=self.instance.vehicle_id)
            )
            self.fields['driver'].queryset = Driver.objects.filter(
                db_models.Q(status=Driver.DriverStatus.AVAILABLE) |
                db_models.Q(pk=self.instance.driver_id)
            )
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(status=Vehicle.VehicleStatus.AVAILABLE)
            self.fields['driver'].queryset = Driver.objects.filter(status=Driver.DriverStatus.AVAILABLE)

        # Help texts
        self.fields['customer'].help_text = "Select the customer for this trip"
        self.fields['commodity_type'].help_text = "Type of goods being transported"
        self.fields['route'].help_text = "Choose the route for this trip"
        self.fields['vehicle'].help_text = "Assign a vehicle to this trip"
        self.fields['driver'].help_text = "Assign a driver to this trip"
        self.fields['quantity'].help_text = "Quantity: liters for Fuel, kg for Goods"
        self.fields['km_start'].help_text = "Starting odometer reading"
        self.fields['km_end'].help_text = "Ending odometer reading (can be filled later)"
        self.fields['fuel_issued'].help_text = "Amount of fuel provided (liters)"
        self.fields['fuel_cost'].help_text = "Cost of fuel for the trip"
        self.fields['other_expenses'].help_text = "Any additional expenses"
        self.fields['revenue'].help_text = "Revenue generated from this trip"

        # Make financial fields optional for creation
        for f in ('km_end', 'fuel_issued', 'fuel_cost', 'other_expenses', 'revenue', 'quantity'):
            self.fields[f].required = False

    def clean_km_end(self):
        km_start = self.cleaned_data.get('km_start')
        km_end = self.cleaned_data.get('km_end')
        if km_start is not None and km_end is not None and km_end < km_start:
            raise ValidationError("End kilometer reading must be greater than start reading.")
        return km_end

    def clean_fuel_cost(self):
        fuel_issued = self.cleaned_data.get('fuel_issued')
        fuel_cost = self.cleaned_data.get('fuel_cost')
        if fuel_issued and fuel_cost:
            if fuel_issued > 0 and fuel_cost == 0:
                raise ValidationError("Fuel cost must be provided when fuel is issued.")
        return fuel_cost

    def clean_vehicle(self):
        vehicle = self.cleaned_data.get('vehicle')
        if not vehicle:
            return vehicle
        # On edit: allow the already-assigned vehicle
        if self.instance and self.instance.pk and self.instance.vehicle_id == vehicle.pk:
            return vehicle
        if vehicle.status != Vehicle.VehicleStatus.AVAILABLE:
            raise ValidationError(f"Vehicle {vehicle} is not available for assignment.")
        return vehicle

    def clean_driver(self):
        driver = self.cleaned_data.get('driver')
        if not driver:
            return driver
        if self.instance and self.instance.pk and self.instance.driver_id == driver.pk:
            return driver
        if driver.status != Driver.DriverStatus.AVAILABLE:
            raise ValidationError(f"Driver {driver} is not available for assignment.")
        return driver


class TripStatusUpdateForm(forms.ModelForm):
    """Simple form for updating just the trip status"""

    class Meta:
        model = Trip
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': INPUT_CSS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].help_text = "Update the current status of this trip"