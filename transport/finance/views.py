from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.http import JsonResponse

from .models import Payment, Expense
from .forms import PaymentForm, ExpenseForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']


class FinanceOverviewView(StaffRequiredMixin, ListView):
    """Overview of financial data with key metrics"""
    model = Payment
    template_name = 'transport/finance/overview.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        return Payment.objects.select_related('trip').order_by('-payment_date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Financial statistics
        total_payments = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        net_profit = total_payments - total_expenses
        
        # Calculate profit margin percentage
        profit_margin_percentage = 0
        if total_payments > 0:
            profit_margin_percentage = (net_profit / total_payments) * 100
        
        context.update({
            'total_revenue': total_payments,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'profit_margin_percentage': profit_margin_percentage,
            'payment_count': Payment.objects.count(),
            'expense_count': Expense.objects.count(),
            'recent_expenses': Expense.objects.order_by('-expense_date')[:10],
            'avg_payment': Payment.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
            'avg_expense': Expense.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
        })
        
        return context


class PaymentListView(StaffRequiredMixin, ListView):
    """List view for payments with filtering"""
    model = Payment
    template_name = 'transport/finance/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.select_related('trip').all()
        
        # Filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')
        search = self.request.GET.get('search')
        
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        if search:
            queryset = queryset.filter(
                Q(trip__order_number__icontains=search) |
                Q(reference__icontains=search)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        payments = Payment.objects.all()
        context.update({
            'total_payments': payments.count(),
            'total_amount': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'avg_amount': payments.aggregate(Avg('amount'))['amount__avg'] or 0,
            
            # Filter values
            'current_date_from': self.request.GET.get('date_from'),
            'current_date_to': self.request.GET.get('date_to'),
            'current_min_amount': self.request.GET.get('min_amount'),
            'current_max_amount': self.request.GET.get('max_amount'),
            'current_search': self.request.GET.get('search'),
        })
        
        return context


class PaymentDetailView(StaffRequiredMixin, DetailView):
    """Detail view for a payment"""
    model = Payment
    template_name = 'transport/finance/payments/detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'trip__customer', 'trip__vehicle', 'trip__driver', 'trip__route'
        )


class PaymentCreateView(StaffRequiredMixin, CreateView):
    """Create view for payments"""
    model = Payment
    form_class = PaymentForm
    template_name = 'transport/finance/payments/create.html'

    def get_success_url(self):
        messages.success(self.request, 'Payment recorded successfully!')
        return reverse_lazy('transport:finance:payment-detail', kwargs={'pk': self.object.pk})


class PaymentUpdateView(StaffRequiredMixin, UpdateView):
    """Update view for payments"""
    model = Payment
    form_class = PaymentForm
    template_name = 'transport/finance/payments/edit.html'
    context_object_name = 'payment'

    def get_queryset(self):
        return super().get_queryset().select_related('trip')

    def get_success_url(self):
        messages.success(self.request, 'Payment updated successfully!')
        return reverse_lazy('transport:finance:payment-detail', kwargs={'pk': self.object.pk})


class ExpenseListView(StaffRequiredMixin, ListView):
    """List view for expenses with filtering"""
    model = Expense
    template_name = 'transport/finance/expenses/list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Expense.objects.select_related('trip').all()
        
        # Filtering
        category = self.request.GET.get('category')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        if date_from:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(expense_date__lte=date_to)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        if search:
            queryset = queryset.filter(
                Q(category__icontains=search) |
                Q(description__icontains=search) |
                Q(trip__order_number__icontains=search)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        expenses = Expense.objects.all()
        context.update({
            'total_expenses': expenses.count(),
            'total_amount': expenses.aggregate(Sum('amount'))['amount__sum'] or 0,
            'avg_amount': expenses.aggregate(Avg('amount'))['amount__avg'] or 0,
            'categories': expenses.values_list('category', flat=True).distinct(),
            
            # Filter values
            'current_category': self.request.GET.get('category'),
            'current_date_from': self.request.GET.get('date_from'),
            'current_date_to': self.request.GET.get('date_to'),
            'current_min_amount': self.request.GET.get('min_amount'),
            'current_max_amount': self.request.GET.get('max_amount'),
            'current_search': self.request.GET.get('search'),
        })
        
        return context


class ExpenseDetailView(StaffRequiredMixin, DetailView):
    """Detail view for an expense"""
    model = Expense
    template_name = 'transport/finance/expenses/detail.html'
    context_object_name = 'expense'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'trip__customer', 'trip__vehicle', 'trip__driver', 'trip__route'
        )


class ExpenseCreateView(StaffRequiredMixin, CreateView):
    """Create view for expenses"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'transport/finance/expenses/create.html'

    def get_success_url(self):
        messages.success(self.request, 'Expense recorded successfully!')
        return reverse_lazy('transport:finance:expense-detail', kwargs={'pk': self.object.pk})


class ExpenseUpdateView(StaffRequiredMixin, UpdateView):
    """Update view for expenses"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'transport/finance/expenses/edit.html'
    context_object_name = 'expense'

    def get_queryset(self):
        return super().get_queryset().select_related('trip')

    def get_success_url(self):
        messages.success(self.request, 'Expense updated successfully!')
        return reverse_lazy('transport:finance:expense-detail', kwargs={'pk': self.object.pk})