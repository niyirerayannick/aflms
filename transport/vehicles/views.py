# Vehicle Module Views
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils.decorators import method_decorator
from django.utils import timezone

from .models import Vehicle
from .forms import VehicleForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']


class VehicleListView(StaffRequiredMixin, ListView):
    model = Vehicle
    template_name = 'transport/vehicles/list.html'
    context_object_name = 'vehicles'
    paginate_by = 20

    def get_queryset(self):
        queryset = Vehicle.objects.all()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(plate_number__icontains=search) | 
                Q(model__icontains=search) | 
                Q(make__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Fleet Management'
        context['total_vehicles'] = Vehicle.objects.count()
        context['available_vehicles'] = Vehicle.objects.filter(status='AVAILABLE').count()
        context['assigned_vehicles'] = Vehicle.objects.filter(status='ASSIGNED').count()
        context['maintenance_vehicles'] = Vehicle.objects.filter(status='MAINTENANCE').count()
        context['status_choices'] = Vehicle.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['today'] = timezone.now().date()
        context['warning_date'] = timezone.now().date() + timedelta(days=30)
        return context


class VehicleDetailView(StaffRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'transport/vehicles/detail.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.get_object()
        today = timezone.now().date()
        
        # Current tab
        tab = self.request.GET.get('tab', 'overview')
        context['current_tab'] = tab
        context['today'] = today
        context['warning_date'] = today + timedelta(days=30)
        
        # Recent trips via reverse relation
        trips = vehicle.trips.all().order_by('-created_at')
        context['recent_trips'] = trips[:10]
        context['total_trips'] = trips.count()
        
        # Trip-based metrics
        trip_stats = trips.aggregate(
            total_revenue=Sum('revenue'),
            total_fuel_cost=Sum('fuel_cost'),
            total_distance=Sum('distance'),
            total_cost=Sum('total_cost'),
            total_profit=Sum('profit'),
            avg_cost_per_km=Avg('cost_per_km'),
        )
        
        context['performance_metrics'] = {
            'total_trips': trips.count(),
            'total_revenue': trip_stats['total_revenue'] or 0,
            'total_fuel_cost': trip_stats['total_fuel_cost'] or 0,
            'total_distance': trip_stats['total_distance'] or 0,
            'total_cost': trip_stats['total_cost'] or 0,
            'total_profit': trip_stats['total_profit'] or 0,
            'avg_cost_per_km': trip_stats['avg_cost_per_km'] or 0,
        }
        
        # Maintenance records
        maintenance_records = vehicle.maintenance_records.all().order_by('-service_date')
        context['maintenance_records'] = maintenance_records[:5]
        maintenance_stats = maintenance_records.aggregate(
            total_maintenance_cost=Sum('cost'),
            total_downtime=Sum('downtime_days'),
        )
        context['total_maintenance_cost'] = maintenance_stats['total_maintenance_cost'] or 0
        context['total_downtime_days'] = maintenance_stats['total_downtime'] or 0
        
        # Fuel entries
        fuel_entries = vehicle.trips.aggregate(
            total_fuel=Sum('fuel_issued'),
            total_fuel_cost=Sum('fuel_cost'),
        )
        context['total_fuel_issued'] = fuel_entries['total_fuel'] or 0
        context['total_fuel_cost'] = fuel_entries['total_fuel_cost'] or 0
        
        # Document status alerts
        alerts = []
        if vehicle.insurance_expiry < today:
            alerts.append({'type': 'danger', 'message': 'Insurance has EXPIRED!'})
        elif vehicle.insurance_expiry < today + timedelta(days=30):
            days_left = (vehicle.insurance_expiry - today).days
            alerts.append({'type': 'warning', 'message': f'Insurance expires in {days_left} days'})
        
        if vehicle.inspection_expiry < today:
            alerts.append({'type': 'danger', 'message': 'Inspection has EXPIRED!'})
        elif vehicle.inspection_expiry < today + timedelta(days=30):
            days_left = (vehicle.inspection_expiry - today).days
            alerts.append({'type': 'warning', 'message': f'Inspection expires in {days_left} days'})
        
        if vehicle.current_odometer >= vehicle.next_service_km:
            km_over = int(vehicle.current_odometer - vehicle.next_service_km)
            alerts.append({'type': 'danger', 'message': f'Service OVERDUE by {km_over:,} km'})
        else:
            km_left = int(vehicle.next_service_km - vehicle.current_odometer)
            if km_left < 1000:
                alerts.append({'type': 'warning', 'message': f'Service due in {km_left:,} km'})
        
        context['alerts'] = alerts
        
        return context


class VehicleCreateView(StaffRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transport/vehicles/create.html'
    success_url = reverse_lazy('transport:vehicles:list')

    def form_valid(self, form):
        messages.success(self.request, f'Vehicle {form.instance.plate_number} created successfully!')
        return super().form_valid(form)


class VehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transport/vehicles/edit.html'
    
    def get_success_url(self):
        return reverse('transport:vehicles:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = self.get_object()
        context['today'] = timezone.now().date()
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Vehicle {form.instance.plate_number} updated successfully!')
        return super().form_valid(form)


@login_required  
def vehicle_quick_status(request, vehicle_id):
    """AJAX view to quickly update vehicle status"""
    if not request.user.role in ['superadmin', 'admin', 'manager']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Vehicle.STATUS_CHOICES):
        vehicle.status = new_status
        vehicle.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Vehicle status updated to {vehicle.get_status_display()}'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})