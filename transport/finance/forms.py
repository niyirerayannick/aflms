from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Payment, Expense
from transport.trips.models import Trip


class PaymentForm(forms.ModelForm):
    """Form for creating and updating payments"""
    
    class Meta:
        model = Payment
        fields = ['trip', 'amount', 'payment_date', 'reference']
        widgets = {
            'trip': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'step': '0.01',
                'min': '0',
                'required': True,
                'placeholder': '0.00'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'type': 'date',
                'required': True
            }),
            'reference': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Payment reference number or notes'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter trips that can receive payments
        self.fields['trip'].queryset = Trip.objects.filter(
            status__in=[Trip.TripStatus.DELIVERED, Trip.TripStatus.CLOSED]
        ).select_related('customer', 'route')
        
        # Set help texts
        self.fields['trip'].help_text = "Select the trip this payment is for"
        self.fields['amount'].help_text = "Payment amount received"
        self.fields['payment_date'].help_text = "Date the payment was received"
        self.fields['reference'].help_text = "Payment reference, receipt number, or transaction notes"

    def clean_payment_date(self):
        payment_date = self.cleaned_data.get('payment_date')
        
        if payment_date and payment_date > timezone.now().date():
            raise ValidationError("Payment date cannot be in the future.")
        
        return payment_date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount and amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        
        return amount

    def clean(self):
        cleaned_data = super().clean()
        trip = cleaned_data.get('trip')
        amount = cleaned_data.get('amount')
        
        if trip and amount:
            # Check if payment amount is reasonable compared to trip revenue
            if trip.revenue and amount > trip.revenue * 1.1:  # Allow 10% buffer
                raise ValidationError(
                    f"Payment amount (${amount}) seems high compared to trip revenue (${trip.revenue}). "
                    "Please verify the amount."
                )
        
        return cleaned_data


class ExpenseForm(forms.ModelForm):
    """Form for creating and updating expenses"""
    
    # Common expense categories
    CATEGORY_CHOICES = [
        ('Fuel', 'Fuel'),
        ('Maintenance', 'Vehicle Maintenance'),
        ('Tolls', 'Road Tolls'),
        ('Parking', 'Parking Fees'),
        ('Insurance', 'Insurance'),
        ('Permits', 'Permits & Licenses'),
        ('Repairs', 'Vehicle Repairs'),
        ('Accommodation', 'Driver Accommodation'),
        ('Meals', 'Driver Meals'),
        ('Office', 'Office Expenses'),
        ('Other', 'Other Expenses'),
    ]
    
    category = forms.ChoiceField(
        choices=[('', 'Select category')] + CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'required': True
        })
    )
    
    class Meta:
        model = Expense
        fields = ['trip', 'category', 'amount', 'expense_date', 'description']
        widgets = {
            'trip': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'step': '0.01',
                'min': '0',
                'required': True,
                'placeholder': '0.00'
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'type': 'date',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'rows': 3,
                'placeholder': 'Detailed description of the expense...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Trip is optional for expenses (some expenses are general)
        self.fields['trip'].queryset = Trip.objects.all().select_related(
            'customer', 'route', 'vehicle'
        )
        self.fields['trip'].required = False
        
        # Set help texts
        self.fields['trip'].help_text = "Optionally link this expense to a specific trip"
        self.fields['category'].help_text = "Type of expense"
        self.fields['amount'].help_text = "Expense amount"
        self.fields['expense_date'].help_text = "Date the expense was incurred"
        self.fields['description'].help_text = "Detailed description of what the expense was for"

    def clean_expense_date(self):
        expense_date = self.cleaned_data.get('expense_date')
        
        if expense_date and expense_date > timezone.now().date():
            raise ValidationError("Expense date cannot be in the future.")
        
        return expense_date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount and amount <= 0:
            raise ValidationError("Expense amount must be greater than zero.")
        
        return amount

    def clean_description(self):
        description = self.cleaned_data.get('description')
        
        if description and len(description.strip()) < 10:
            raise ValidationError("Please provide a more detailed description (at least 10 characters).")
        
        return description