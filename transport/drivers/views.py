# Driver Module Views
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
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings as app_settings
from django.template.loader import render_to_string

from accounts.models import User as AuthUser
from .models import Driver
from .forms import DriverForm


def generate_password(length=10):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    # Ensure at least one of each type
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

class DriverListView(StaffRequiredMixin, ListView):
    model = Driver
    template_name = 'transport/drivers/list.html'
    context_object_name = 'drivers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Driver.objects.all()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(license_number__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Driver statistics
        all_drivers = Driver.objects.all()
        context['total_drivers'] = all_drivers.count()
        context['available_drivers'] = all_drivers.filter(status='AVAILABLE').count()
        context['assigned_drivers'] = all_drivers.filter(status='ASSIGNED').count()
        
        # License alerts (expiring in next 30 days)
        from datetime import timedelta
        next_month = timezone.now().date() + timedelta(days=30)
        context['license_expiring'] = all_drivers.filter(license_expiry__lte=next_month).count()
        
        context['status_choices'] = Driver.STATUS_CHOICES
        return context

class DriverDetailView(StaffRequiredMixin, DetailView):
    model = Driver
    template_name = 'transport/drivers/detail.html'
    context_object_name = 'driver'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        driver = self.get_object()
        
        # Add tabs data
        tab = self.request.GET.get('tab', 'overview')
        context['current_tab'] = tab
        
        # Recent trips — real data from Trip model
        from transport.trips.models import Trip
        driver_trips = Trip.objects.filter(driver=driver).select_related(
            'vehicle', 'customer', 'route', 'commodity_type',
        ).order_by('-created_at')
        context['recent_trips'] = driver_trips[:10]
        
        # Performance metrics — computed from actual trips
        from django.db.models import Sum, Count, Avg
        stats = driver_trips.aggregate(
            total_trips=Count('id'),
            total_distance=Sum('distance'),
            total_revenue=Sum('revenue'),
            total_cost=Sum('total_cost'),
            total_profit=Sum('profit'),
        )
        completed_trips = driver_trips.filter(
            status__in=[Trip.TripStatus.DELIVERED, Trip.TripStatus.CLOSED],
        ).count()
        context['performance_metrics'] = {
            'total_trips': stats['total_trips'] or 0,
            'total_distance': stats['total_distance'] or 0,
            'total_revenue': stats['total_revenue'] or 0,
            'total_cost': stats['total_cost'] or 0,
            'total_profit': stats['total_profit'] or 0,
            'completed_trips': completed_trips,
            'safety_score': 100,  # TODO: Calculate from incident reports
        }
        
        # Active trip (ASSIGNED or IN_TRANSIT)
        context['active_trip'] = driver_trips.filter(
            status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT],
        ).first()
        
        # License and document alerts
        from datetime import timedelta
        context['alerts'] = []
        if driver.license_expiry:
            days_until_expiry = (driver.license_expiry - timezone.now().date()).days
            if days_until_expiry <= 30:
                context['alerts'].append({
                    'type': 'warning' if days_until_expiry > 7 else 'danger',
                    'message': f'License expires in {days_until_expiry} days'
                })
        
        return context

class DriverCreateView(StaffRequiredMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'transport/drivers/create.html'
    success_url = reverse_lazy('transport:drivers:list')

    def form_valid(self, form):
        driver = form.save(commit=False)
        create_account = form.cleaned_data.get('create_account', True)
        email = form.cleaned_data.get('email', '')
        
        driver.email = email
        driver.save()
        
        if create_account and email:
            # Check if a user with this email already exists
            existing_user = AuthUser.objects.filter(email=email.lower()).first()
            
            if existing_user:
                # Link existing account to driver
                driver.user = existing_user
                driver.save()
                messages.info(
                    self.request, 
                    f'Driver "{driver.name}" created and linked to existing account ({email}).'
                )
            else:
                # Generate a secure password
                password = generate_password()
                
                # Create user account
                try:
                    user = AuthUser.objects.create_user(
                        email=email.lower(),
                        full_name=driver.name,
                        password=password,
                        role=AuthUser.Role.DRIVER,
                        phone=driver.phone,
                    )
                    
                    # Link user to driver
                    driver.user = user
                    driver.save()
                    
                    # Send email with credentials
                    try:
                        subject = 'Your Driver Account Has Been Created'
                        message = (
                            f"Hello {driver.name},\n\n"
                            f"Your driver account has been created in the Transport Management System.\n\n"
                            f"Here are your login credentials:\n"
                            f"  Email: {email}\n"
                            f"  Password: {password}\n\n"
                            f"Phone registered: {driver.phone}\n\n"
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
                            f'Driver "{driver.name}" created successfully! '
                            f'Account credentials sent to {email} and phone {driver.phone}.'
                        )
                    except Exception as e:
                        messages.warning(
                            self.request,
                            f'Driver "{driver.name}" created and account set up, '
                            f'but email could not be sent: {str(e)}. '
                            f'Generated password: {password}'
                        )
                        
                except Exception as e:
                    messages.warning(
                        self.request,
                        f'Driver "{driver.name}" created, but account creation failed: {str(e)}'
                    )
        else:
            messages.success(self.request, f'Driver "{driver.name}" created successfully (no account created).')
        
        return redirect(self.success_url)

class DriverUpdateView(StaffRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'transport/drivers/edit.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Remove create_account field on edit
        if 'create_account' in form.fields:
            del form.fields['create_account']
        # Pre-fill email from the model
        if self.object and self.object.email:
            form.fields['email'].initial = self.object.email
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['driver'] = self.object
        return context

    def get_success_url(self):
        return reverse_lazy('transport:drivers:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Driver {form.cleaned_data["name"]} updated successfully!')
        return super().form_valid(form)

@login_required  
def driver_quick_status(request, driver_id):
    """AJAX view to quickly update driver status"""
    if not request.user.role in ['superadmin', 'admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    driver = get_object_or_404(Driver, id=driver_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Driver.STATUS_CHOICES):
        driver.status = new_status
        driver.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Driver status updated to {driver.get_status_display()}'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})