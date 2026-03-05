from django import forms
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Order, OrderNote, OrderDocument
from transport.customers.models import Customer
from transport.routes.models import Route
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver


class OrderForm(forms.ModelForm):
    """Form for creating and editing orders"""
    
    class Meta:
        model = Order
        fields = [
            'customer', 'commodity_type', 'commodity_description', 'quantity',
            'estimated_weight', 'estimated_volume', 'route', 'pickup_address',
            'delivery_address', 'pickup_contact', 'delivery_contact',
            'requested_pickup_date', 'requested_delivery_date', 'quoted_price',
            'estimated_cost', 'special_instructions', 'requires_insurance',
            'requires_special_handling', 'fragile_items', 'priority_level'
        ]
        
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'commodity_type': forms.Select(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'commodity_description': forms.Textarea(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 3
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., 50 tons, 100 boxes'
            }),
            'estimated_weight': forms.NumberInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01'
            }),
            'estimated_volume': forms.NumberInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01'
            }),
            'route': forms.Select(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'pickup_address': forms.Textarea(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 2
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 2
            }),
            'pickup_contact': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Name and phone number'
            }),
            'delivery_contact': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Name and phone number'
            }),
            'requested_pickup_date': forms.DateTimeInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'requested_delivery_date': forms.DateTimeInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'quoted_price': forms.NumberInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01'
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 3
            }),
            'priority_level': forms.Select(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum dates for pickup and delivery
        min_date = timezone.now()
        self.fields['requested_pickup_date'].widget.attrs['min'] = min_date.strftime('%Y-%m-%dT%H:%M')
        self.fields['requested_delivery_date'].widget.attrs['min'] = min_date.strftime('%Y-%m-%dT%H:%M')
        
        # Add help text
        self.fields['estimated_weight'].help_text = "Weight in tons"
        self.fields['estimated_volume'].help_text = "Volume in cubic meters"
        self.fields['quoted_price'].help_text = "Price quoted to customer"
        self.fields['estimated_cost'].help_text = "Estimated operational cost"
    
    def clean(self):
        cleaned_data = super().clean()
        pickup_date = cleaned_data.get('requested_pickup_date')
        delivery_date = cleaned_data.get('requested_delivery_date')
        quoted_price = cleaned_data.get('quoted_price')
        estimated_cost = cleaned_data.get('estimated_cost')
        
        # Validate dates
        if pickup_date and delivery_date:
            if pickup_date >= delivery_date:
                raise forms.ValidationError("Delivery date must be after pickup date")
            
            if pickup_date < timezone.now():
                raise forms.ValidationError("Pickup date cannot be in the past")
        
        # Validate pricing
        if quoted_price and estimated_cost:
            if quoted_price < estimated_cost:
                # Warning, not error - allow but warn
                self.add_error('quoted_price', 'Warning: Quoted price is less than estimated cost (negative profit)')
        
        return cleaned_data


class OrderApprovalForm(forms.ModelForm):
    """Form for approving or rejecting orders"""
    
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('request_changes', 'Request Changes')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300'
        })
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'rows': 4,
            'placeholder': 'Add notes for this approval decision...'
        }),
        required=False
    )
    
    class Meta:
        model = Order
        fields = ['action', 'notes']


class OrderAssignmentForm(forms.Form):
    """Form for assigning orders to vehicles and drivers"""
    
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(status='available'),
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    driver = forms.ModelChoiceField(
        queryset=Driver.objects.filter(is_available=True),
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    estimated_departure = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'datetime-local'
        })
    )
    
    assignment_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Notes for this assignment...'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum departure time to now
        min_time = timezone.now()
        self.fields['estimated_departure'].widget.attrs['min'] = min_time.strftime('%Y-%m-%dT%H:%M')


class OrderNoteForm(forms.ModelForm):
    """Form for adding notes to orders"""
    
    class Meta:
        model = OrderNote
        fields = ['note', 'is_internal']
        
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Add a note...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded'
            })
        }


class OrderDocumentForm(forms.ModelForm):
    """Form for uploading documents to orders"""
    
    class Meta:
        model = OrderDocument
        fields = ['name', 'document_type', 'file']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Document name'
            }),
            'document_type': forms.Select(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            })
        }


class OrderFilterForm(forms.Form):
    """Form for filtering orders in list view"""
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Order.Status.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    commodity_type = forms.ChoiceField(
        choices=[('', 'All Commodities')] + Order.CommodityType.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    priority_level = forms.ChoiceField(
        choices=[('', 'All Priorities'), ('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search by order number, customer, or description...'
        })
    )