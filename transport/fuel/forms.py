from django import forms
from .models import FuelEntry, FuelStation


INPUT_CSS = (
    "mt-1 block w-full border-gray-300 rounded-md shadow-sm "
    "focus:ring-blue-500 focus:border-blue-500"
)


class FuelStationForm(forms.ModelForm):
    """Form for creating and updating fuel stations"""

    class Meta:
        model = FuelStation
        fields = ['name', 'location', 'contact_person', 'phone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Station name (e.g. Rubis Kicukiro)',
            }),
            'location': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Address or area',
            }),
            'contact_person': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Contact person name',
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': '+250 7XX XXX XXX',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }

class FuelEntryForm(forms.ModelForm):
    """Form for creating and updating fuel entries"""
    
    class Meta:
        model = FuelEntry
        fields = [
            'trip', 'liters', 'price_per_liter', 'station', 'date', 'invoice'
        ]
        widgets = {
            'trip': forms.Select(attrs={
                'class': INPUT_CSS,
            }),
            'liters': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Enter liters of fuel',
                'step': '0.01',
                'min': '0'
            }),
            'price_per_liter': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Enter price per liter',
                'step': '0.01',
                'min': '0'
            }),
            'station': forms.Select(attrs={
                'class': INPUT_CSS,
            }),
            'date': forms.DateInput(attrs={
                'class': INPUT_CSS,
                'type': 'date'
            }),
            'invoice': forms.ClearableFileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 '
                         'file:rounded-md file:border-0 file:text-sm file:font-semibold '
                         'file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
            }),
        }
        labels = {
            'trip': 'Trip',
            'liters': 'Liters',
            'price_per_liter': 'Price per Liter',
            'station': 'Fuel Station',
            'date': 'Date',
            'invoice': 'Supporting Document',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['station'].queryset = FuelStation.objects.filter(is_active=True)
        self.fields['station'].empty_label = '-- Select a fuel station --'
        self.fields['invoice'].required = False

    def clean_liters(self):
        liters = self.cleaned_data.get('liters')
        if liters is not None and liters <= 0:
            raise forms.ValidationError("Liters must be greater than zero.")
        return liters

    def clean_price_per_liter(self):
        price = self.cleaned_data.get('price_per_liter')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price per liter must be greater than zero.")
        return price

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date:
            from django.utils import timezone
            if date > timezone.now().date():
                raise forms.ValidationError("Date cannot be in the future.")
        return date

    def clean_invoice(self):
        invoice = self.cleaned_data.get('invoice')
        if invoice and hasattr(invoice, 'size'):
            if invoice.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError("File size must be under 10 MB.")
        return invoice


class FuelSearchForm(forms.Form):
    """Form for searching fuel entries"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search by trip number or fuel station...'
        })
    )
    station = forms.ModelChoiceField(
        queryset=FuelStation.objects.filter(is_active=True),
        required=False,
        empty_label='All Stations',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        })
    )