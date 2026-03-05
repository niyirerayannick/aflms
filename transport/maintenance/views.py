from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone

from .models import MaintenanceRecord
from .forms import MaintenanceRecordForm
from transport.vehicles.models import Vehicle


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']


class MaintenanceListView(StaffRequiredMixin, ListView):
    """List view for maintenance records with filtering and search"""
    model = MaintenanceRecord
    template_name = 'transport/maintenance/list.html'
    context_object_name = 'maintenance_records'
    paginate_by = 20

    def get_queryset(self):
        queryset = MaintenanceRecord.objects.select_related('vehicle').all()
        
        # Filtering
        vehicle_id = self.request.GET.get('vehicle')
        service_type = self.request.GET.get('service_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if service_type:
            queryset = queryset.filter(service_type__icontains=service_type)
        if date_from:
            queryset = queryset.filter(service_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(service_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(vehicle__plate_number__icontains=search) |
                Q(vehicle__vehicle_type__icontains=search) |
                Q(service_type__icontains=search) |
                Q(workshop__icontains=search)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        records = MaintenanceRecord.objects.all()
        context.update({
            'total_records': records.count(),
            'total_cost': records.aggregate(Sum('cost'))['cost__sum'] or 0,
            'avg_cost': records.aggregate(Avg('cost'))['cost__avg'] or 0,
            'vehicles_in_maintenance': Vehicle.objects.filter(
                status=Vehicle.VehicleStatus.MAINTENANCE
            ).count(),
            'vehicles': Vehicle.objects.all(),
            'service_types': MaintenanceRecord.objects.values_list(
                'service_type', flat=True
            ).distinct(),
            
            # Filter values
            'current_vehicle': self.request.GET.get('vehicle'),
            'current_service_type': self.request.GET.get('service_type'),
            'current_date_from': self.request.GET.get('date_from'),
            'current_date_to': self.request.GET.get('date_to'),
            'current_search': self.request.GET.get('search'),
        })
        
        return context


class MaintenanceDetailView(StaffRequiredMixin, DetailView):
    """Detail view for a maintenance record"""
    model = MaintenanceRecord
    template_name = 'transport/maintenance/detail.html'
    context_object_name = 'record'

    def get_queryset(self):
        return MaintenanceRecord.objects.select_related('vehicle')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.get_object()
        
        # Related maintenance records for this vehicle
        context['related_records'] = MaintenanceRecord.objects.filter(
            vehicle=record.vehicle
        ).select_related('vehicle').exclude(id=record.id).order_by('-service_date')[:5]
        
        return context


class MaintenanceCreateView(StaffRequiredMixin, CreateView):
    """Create view for maintenance records"""
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'transport/maintenance/create.html'

    def get_success_url(self):
        messages.success(self.request, 'Maintenance record created successfully!')
        return reverse_lazy('transport:maintenance:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Maintenance record has been created.')
        return super().form_valid(form)


class MaintenanceUpdateView(StaffRequiredMixin, UpdateView):
    """Update view for maintenance records"""
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'transport/maintenance/edit.html'

    def get_success_url(self):
        messages.success(self.request, 'Maintenance record updated successfully!')
        return reverse_lazy('transport:maintenance:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Maintenance record has been updated.')
        return super().form_valid(form)