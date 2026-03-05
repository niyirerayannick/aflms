# Trip Module Views
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Trip
from .forms import TripForm
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in [
            'superadmin', 'admin', 'manager',
        ]


# ------------------------------------------------------------------ List
class TripListView(StaffRequiredMixin, ListView):
    model = Trip
    template_name = 'transport/trips/list.html'
    context_object_name = 'trips'
    paginate_by = 20

    def get_queryset(self):
        qs = Trip.objects.select_related(
            'vehicle', 'driver', 'customer', 'route', 'commodity_type',
        )

        # Role-based filtering
        user = self.request.user
        if user.role == 'driver':
            qs = qs.filter(driver__user=user)
        elif user.role == 'client':
            qs = qs.filter(customer__user=user)

        # Query-string filters
        status = self.request.GET.get('status')
        driver_id = self.request.GET.get('driver')
        vehicle_id = self.request.GET.get('vehicle')
        search = self.request.GET.get('search')

        if status:
            qs = qs.filter(status=status)
        if driver_id:
            qs = qs.filter(driver_id=driver_id)
        if vehicle_id:
            qs = qs.filter(vehicle_id=vehicle_id)
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(customer__company_name__icontains=search) |
                Q(driver__name__icontains=search) |
                Q(vehicle__plate_number__icontains=search)
            )

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_trips = Trip.objects.all()
        ctx['total_trips'] = all_trips.count()
        ctx['draft_trips'] = all_trips.filter(status=Trip.TripStatus.DRAFT).count()
        ctx['active_trips'] = all_trips.filter(
            status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT],
        ).count()
        ctx['delivered_trips'] = all_trips.filter(status=Trip.TripStatus.DELIVERED).count()
        ctx['total_revenue'] = all_trips.aggregate(total=Sum('revenue'))['total'] or 0

        # Filter choices
        ctx['status_choices'] = Trip.STATUS_CHOICES
        ctx['drivers'] = Driver.objects.all().order_by('name')
        ctx['vehicles'] = Vehicle.objects.all().order_by('plate_number')
        return ctx


# ------------------------------------------------------------------ Detail
class TripDetailView(StaffRequiredMixin, DetailView):
    model = Trip
    template_name = 'transport/trips/detail.html'
    context_object_name = 'trip'

    def get_queryset(self):
        return Trip.objects.select_related(
            'vehicle', 'driver', 'customer', 'route', 'commodity_type',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trip = self.object

        # Workflow permission flags (uppercase statuses)
        ctx['can_approve'] = trip.status == Trip.TripStatus.DRAFT
        ctx['can_assign'] = trip.status == Trip.TripStatus.APPROVED
        ctx['can_start'] = trip.status == Trip.TripStatus.ASSIGNED
        ctx['can_deliver'] = trip.status == Trip.TripStatus.IN_TRANSIT
        ctx['can_close'] = trip.status == Trip.TripStatus.DELIVERED
        ctx['can_edit'] = trip.status in (Trip.TripStatus.DRAFT, Trip.TripStatus.APPROVED)
        return ctx


# ------------------------------------------------------------------ Create
class TripCreateView(StaffRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'transport/trips/create.html'
    success_url = reverse_lazy('transport:trips:list')

    def get_initial(self):
        initial = super().get_initial()
        driver_id = self.request.GET.get('driver')
        vehicle_id = self.request.GET.get('vehicle')
        if driver_id:
            initial['driver'] = driver_id
        if vehicle_id:
            initial['vehicle'] = vehicle_id
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Trip {self.object.order_number} created successfully!',
        )
        return response


# ------------------------------------------------------------------ Update
class TripUpdateView(StaffRequiredMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'transport/trips/edit.html'

    def get_success_url(self):
        return reverse_lazy('transport:trips:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Trip {self.object.order_number} updated successfully!',
        )
        return response


# ------------------------------------------------------------------ Status
# Valid workflow transitions (uppercase model values)
VALID_TRANSITIONS = {
    Trip.TripStatus.DRAFT: [Trip.TripStatus.APPROVED],
    Trip.TripStatus.APPROVED: [Trip.TripStatus.ASSIGNED],
    Trip.TripStatus.ASSIGNED: [Trip.TripStatus.IN_TRANSIT],
    Trip.TripStatus.IN_TRANSIT: [Trip.TripStatus.DELIVERED],
    Trip.TripStatus.DELIVERED: [Trip.TripStatus.CLOSED],
    Trip.TripStatus.CLOSED: [],
}


@login_required
@require_POST
def update_trip_status(request, trip_id):
    """POST view to update trip status through the workflow."""
    if request.user.role not in ('superadmin', 'admin', 'manager', 'driver'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        messages.error(request, 'Permission denied.')
        return redirect('transport:trips:list')

    trip = get_object_or_404(Trip, pk=trip_id)
    new_status = request.POST.get('status', '').upper()

    allowed = VALID_TRANSITIONS.get(trip.status, [])
    if new_status not in allowed:
        msg = (
            f'Cannot change status from {trip.get_status_display()} '
            f'to {dict(Trip.STATUS_CHOICES).get(new_status, new_status)}.'
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': msg})
        messages.error(request, msg)
        return redirect('transport:trips:detail', pk=trip.pk)

    trip.status = new_status
    trip.save()

    success_msg = f'Trip status updated to {trip.get_status_display()}.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': success_msg})
    messages.success(request, success_msg)
    return redirect('transport:trips:detail', pk=trip.pk)