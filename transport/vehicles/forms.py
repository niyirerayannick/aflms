from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    """Form for creating and updating vehicles"""
    
    class Meta:
        model = Vehicle
        fields = [
            'plate_number', 'vehicle_type', 'capacity', 'current_odometer',
            'status', 'insurance_expiry', 'inspection_expiry', 
            'service_interval_km', 'last_service_km'
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Enter plate number'
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.5',
                'min': '0.5',
                'placeholder': 'Capacity in tons'
            }),
            'current_odometer': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '1',
                'min': '0',
                'placeholder': 'Current odometer reading'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'insurance_expiry': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date',
            }),
            'inspection_expiry': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date',
            }),
            'service_interval_km': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '1000',
                'step': '1000',
                'placeholder': 'Service interval in kilometers'
            }),
            'last_service_km': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',  
                'min': '0',
                'placeholder': 'Last service odometer reading'
            })
        }