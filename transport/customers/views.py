# Customer Module Views
import string
import secrets
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings as app_settings

from accounts.models import User as AuthUser
from .models import Customer
from .forms import CustomerForm
from transport.trips.models import Trip


def generate_password(length=10):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    password = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        secrets.choice('!@#$%') +
        password[4:]
    )
    return password

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']

class CustomerListView(StaffRequiredMixin, ListView):
    model = Customer
    template_name = 'transport/customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Customer.objects.all()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Customer statistics
        all_customers = Customer.objects.all()
        context['total_customers'] = all_customers.count()
        context['active_customers'] = all_customers.filter(status='ACTIVE').count()
        context['inactive_customers'] = all_customers.filter(status='INACTIVE').count() + all_customers.filter(status='SUSPENDED').count()
        
        # Financial metrics - TODO: Implement when Trip model is ready
        context['total_revenue'] = 0  # TODO: Calculate from trips
        context['customers_with_outstanding'] = 0  # TODO: Implement
        
        context['status_choices'] = Customer.STATUS_CHOICES
        return context

class CustomerDetailView(StaffRequiredMixin, DetailView):
    model = Customer
    template_name = 'transport/customers/detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # Add tabs data
        tab = self.request.GET.get('tab', 'overview')
        context['current_tab'] = tab
        
        # View mode (grid or list)
        context['view_mode'] = self.request.GET.get('view', 'list')
        
        # Service history filters
        status_filter = self.request.GET.get('status', '')
        search_query = self.request.GET.get('q', '')
        
        # All trips for this customer
        customer_trips = Trip.objects.filter(customer=customer).select_related(
            'route', 'vehicle', 'driver', 'commodity_type'
        )
        
        # Apply filters
        if status_filter:
            customer_trips = customer_trips.filter(status=status_filter)
        if search_query:
            customer_trips = customer_trips.filter(
                Q(order_number__icontains=search_query) |
                Q(route__origin__icontains=search_query) |
                Q(route__destination__icontains=search_query) |
                Q(vehicle__plate_number__icontains=search_query) |
                Q(driver__name__icontains=search_query)
            )
        
        customer_trips = customer_trips.order_by('-created_at')
        
        # Pagination for service history
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(customer_trips, 12)
        page_obj = paginator.get_page(page_number)
        
        context['service_history'] = page_obj
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['is_paginated'] = page_obj.has_other_pages()
        context['status_filter'] = status_filter
        context['search_query'] = search_query
        context['trip_status_choices'] = Trip.TripStatus.choices
        
        # Customer metrics
        all_trips = Trip.objects.filter(customer=customer)
        completed_trips = all_trips.filter(status__in=['DELIVERED', 'CLOSED'])
        active_trips = all_trips.filter(status__in=['ASSIGNED', 'IN_TRANSIT'])
        
        context['customer_metrics'] = {
            'total_trips': all_trips.count(),
            'completed_trips': completed_trips.count(),
            'active_trips': active_trips.count(),
            'total_revenue': completed_trips.aggregate(total=Sum('revenue'))['total'] or 0,
            'avg_trip_value': completed_trips.aggregate(avg=Avg('revenue'))['avg'] or 0,
            'total_distance': completed_trips.aggregate(total=Sum('distance'))['total'] or 0,
            'outstanding_balance': 0,  # TODO: Calculate outstanding payments
        }
        
        # Recent trips (for overview tab)
        context['recent_trips'] = all_trips[:5]
        
        # Last order date
        last_trip = all_trips.first()
        context['last_order_date'] = last_trip.created_at if last_trip else None
        
        # Payment history placeholder
        context['recent_payments'] = []  # TODO: Add payment model and logic
        
        return context

class CustomerCreateView(StaffRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'transport/customers/create.html'
    success_url = reverse_lazy('transport:customers:list')

    def form_valid(self, form):
        customer = form.save(commit=False)
        create_account = form.cleaned_data.get('create_account', True)
        email = form.cleaned_data.get('email', '')
        
        customer.email = email
        customer.save()
        
        if create_account and email:
            # Check if a user with this email already exists
            existing_user = AuthUser.objects.filter(email=email.lower()).first()
            
            if existing_user:
                customer.user = existing_user
                customer.save()
                messages.info(
                    self.request,
                    f'Customer "{customer.company_name}" created and linked to existing account ({email}).'
                )
            else:
                password = generate_password()
                
                try:
                    user = AuthUser.objects.create_user(
                        email=email.lower(),
                        full_name=customer.contact_person or customer.company_name,
                        password=password,
                        role=AuthUser.Role.CLIENT,
                        phone=customer.phone or '',
                    )
                    
                    customer.user = user
                    customer.save()
                    
                    try:
                        subject = 'Your Client Account Has Been Created'
                        message = (
                            f"Hello {customer.contact_person or customer.company_name},\n\n"
                            f"Your client account has been created in the Transport Management System.\n\n"
                            f"Here are your login credentials:\n"
                            f"  Email: {email}\n"
                            f"  Password: {password}\n\n"
                            f"Company: {customer.company_name}\n"
                            f"Phone: {customer.phone}\n\n"
                            f"Please log in and change your password as soon as possible.\n\n"
                            f"Best regards,\n"
                            f"Transport Management Team"
                        )
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=app_settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        messages.success(
                            self.request,
                            f'Customer "{customer.company_name}" created successfully! '
                            f'Account credentials sent to {email}.'
                        )
                    except Exception as e:
                        messages.warning(
                            self.request,
                            f'Customer "{customer.company_name}" created and account set up, '
                            f'but email could not be sent: {str(e)}. '
                            f'Generated password: {password}'
                        )
                except Exception as e:
                    messages.warning(
                        self.request,
                        f'Customer "{customer.company_name}" created, but account creation failed: {str(e)}'
                    )
        else:
            messages.success(self.request, f'Customer "{customer.company_name}" created successfully (no account created).')
        
        return redirect(self.success_url)

class CustomerUpdateView(StaffRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'transport/customers/edit.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Remove create_account field on edit
        if 'create_account' in form.fields:
            del form.fields['create_account']
        # Pre-fill email from the model
        if self.object and self.object.email:
            form.fields['email'].initial = self.object.email
        return form
    
    def get_success_url(self):
        return reverse_lazy('transport:customers:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Customer {form.instance.company_name} updated successfully!')
        return super().form_valid(form)

@login_required  
def customer_quick_status(request, customer_id):
    """AJAX view to quickly update customer status"""
    if not request.user.role in ['superadmin', 'admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    customer = get_object_or_404(Customer, id=customer_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Customer.STATUS_CHOICES):
        customer.status = new_status
        customer.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Customer status updated to {customer.get_status_display()}'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})