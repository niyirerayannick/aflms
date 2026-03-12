# Core Transport Module Views
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.templatetags.static import static
from accounts.decorators import driver_required
from transport.trips.models import Trip
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver
from transport.customers.models import Customer
from transport.routes.models import Route
from transport.fuel.models import FuelRequest
from transport.vehicles.forms import VehicleForm
from transport.drivers.forms import DriverForm
from transport.customers.forms import CustomerForm
from transport.routes.forms import RouteForm

def _driver_section_context(user):
    driver = get_object_or_404(Driver, user=user)
    assigned_trips = (
        Trip.objects.filter(driver=driver, status=Trip.TripStatus.ASSIGNED)
        .select_related("route", "commodity_type")
        .order_by("-created_at")
    )
    active_trip = (
        Trip.objects.filter(driver=driver, status=Trip.TripStatus.IN_TRANSIT)
        .select_related("route", "commodity_type")
        .first()
    )
    completed_trips = (
        Trip.objects.filter(driver=driver, status=Trip.TripStatus.DELIVERED)
        .select_related("route")
        .order_by("-updated_at")[:5]
    )
    driver_trips = (
        Trip.objects.filter(driver=driver)
        .select_related("route", "commodity_type")
        .order_by("-created_at")[:20]
    )
    fuel_requests = (
        FuelRequest.objects.filter(driver=user)
        .select_related("trip", "station")
        .order_by("-created_at")[:10]
    )

    return {
        "driver": driver,
        "assigned_trips": assigned_trips,
        "active_trip": active_trip,
        "completed_trips": completed_trips,
        "driver_trips": driver_trips,
        "fuel_requests": fuel_requests,
        "assigned_count": assigned_trips.count(),
        "active_count": 1 if active_trip else 0,
        "completed_count": Trip.objects.filter(driver=driver, status=Trip.TripStatus.DELIVERED).count(),
        "fuel_request_count": FuelRequest.objects.filter(driver=user).count(),
    }


@driver_required
def driver_shell(request, tab="dashboard"):
    tab_to_partial = {
        "dashboard": reverse("transport:driver_dashboard_partial"),
        "trips": reverse("transport:driver_trips_partial"),
        "fuel": reverse("transport:driver_fuel_partial"),
        "profile": reverse("transport:driver_profile_partial"),
    }
    if tab not in tab_to_partial:
        tab = "dashboard"

    return render(
        request,
        "transport/driver_base.html",
        {
            "driver_spa": True,
            "initial_tab": tab,
            "initial_partial_url": tab_to_partial[tab],
        },
    )


@driver_required
def driver_dashboard(request):
    return driver_shell(request, tab="dashboard")


@driver_required
def driver_trips(request):
    return driver_shell(request, tab="trips")


@driver_required
def driver_fuel(request):
    return driver_shell(request, tab="fuel")


@driver_required
def driver_profile(request):
    return driver_shell(request, tab="profile")


@driver_required
def driver_dashboard_partial(request):
    context = _driver_section_context(request.user)
    return render(request, "transport/driver/partials/dashboard.html", context)


@driver_required
def driver_trips_partial(request):
    context = _driver_section_context(request.user)
    return render(request, "transport/driver/partials/trips.html", context)


@driver_required
def driver_fuel_partial(request):
    context = _driver_section_context(request.user)
    return render(request, "transport/driver/partials/fuel.html", context)


@driver_required
def driver_profile_partial(request):
    context = _driver_section_context(request.user)
    return render(request, "transport/driver/partials/profile.html", context)


@driver_required
def driver_assignment_state(request):
    driver = get_object_or_404(Driver, user=request.user)
    assigned_qs = Trip.objects.filter(driver=driver, status=Trip.TripStatus.ASSIGNED).order_by("-created_at")
    latest_trip = assigned_qs.first()
    return JsonResponse(
        {
            "assigned_count": assigned_qs.count(),
            "latest_assigned_trip_id": latest_trip.pk if latest_trip else None,
            "latest_assigned_order": latest_trip.order_number if latest_trip else "",
        }
    )


def driver_manifest(request):
    manifest = {
        "name": "AFLMS Driver",
        "short_name": "Driver",
        "start_url": "/transport/driver/",
        "scope": "/transport/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#f1f5f9",
        "theme_color": "#10b981",
        "icons": [
            {
                "src": static("img/Afrilott.png"),
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": static("img/Afrilott.png"),
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    }
    return HttpResponse(
        json.dumps(manifest),
        content_type="application/manifest+json",
    )


def driver_service_worker(_request):
    script = """
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
"""
    return HttpResponse(script, content_type="application/javascript")


@login_required
def driver_dashboard_legacy(request):
    driver = get_object_or_404(Driver, user=request.user)
    
    assigned_trips = Trip.objects.filter(driver=driver, status=Trip.TripStatus.ASSIGNED).order_by('-created_at')
    active_trip = Trip.objects.filter(driver=driver, status=Trip.TripStatus.IN_TRANSIT).first()
    completed_trips = Trip.objects.filter(driver=driver, status=Trip.TripStatus.DELIVERED).order_by('-updated_at')[:5]
    fuel_requests = FuelRequest.objects.filter(driver=request.user).order_by('-created_at')[:5]

    context = {
        'assigned_trips': assigned_trips,
        'active_trip': active_trip,
        'completed_trips': completed_trips,
        'fuel_requests': fuel_requests,
    }
    return render(request, 'transport/driver_dashboard.html', context)

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']

# ============ VEHICLE MANAGEMENT ============

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

class VehicleDetailView(StaffRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'transport/vehicles/detail.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.get_object()
        context['recent_trips'] = Trip.objects.filter(vehicle=vehicle).order_by('-created_at')[:5]
        context['maintenance_alerts'] = []  # TODO: Add maintenance logic
        return context

class VehicleCreateView(StaffRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transport/vehicles/create.html'
    success_url = reverse_lazy('transport:vehicles-list')

    def form_valid(self, form):
        messages.success(self.request, f'Vehicle {form.instance.plate_number} created successfully!')
        return super().form_valid(form)

class VehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transport/vehicles/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:vehicle-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Vehicle {form.instance.plate_number} updated successfully!')
        return super().form_valid(form)

# ============ DRIVER MANAGEMENT ============

class DriverListView(StaffRequiredMixin, ListView):
    model = Driver
    template_name = 'transport/drivers/list.html'
    context_object_name = 'drivers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Driver.objects.select_related('user').all()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(license_number__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

class DriverDetailView(StaffRequiredMixin, DetailView):
    model = Driver
    template_name = 'transport/drivers/detail.html'
    context_object_name = 'driver'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        driver = self.get_object()
        context['recent_trips'] = Trip.objects.filter(driver=driver).order_by('-created_at')[:5]
        context['performance_metrics'] = {
            'total_trips': Trip.objects.filter(driver=driver, status='completed').count(),
            'total_distance': 0,  # TODO: Calculate from completed trips
            'avg_rating': 0,  # TODO: Calculate rating
        }
        return context

class DriverCreateView(StaffRequiredMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'transport/drivers/create.html'
    success_url = reverse_lazy('transport:drivers-list')

    def form_valid(self, form):
        messages.success(self.request, f'Driver {form.instance.user.get_full_name()} created successfully!')
        return super().form_valid(form)

class DriverUpdateView(StaffRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'transport/drivers/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:driver-detail', kwargs={'pk': self.object.pk})

# ============ CUSTOMER MANAGEMENT ============

class CustomerListView(StaffRequiredMixin, ListView):
    model = Customer
    template_name = 'transport/customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Customer.objects.all()
        search = self.request.GET.get('search')
        
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')

class CustomerDetailView(StaffRequiredMixin, DetailView):
    model = Customer
    template_name = 'transport/customers/detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        context['recent_trips'] = Trip.objects.filter(customer=customer).order_by('-created_at')[:5]
        context['payment_summary'] = {
            'total_trips': Trip.objects.filter(customer=customer).count(),
            'total_revenue': 0,  # TODO: Calculate from completed trips
            'outstanding_balance': 0,  # TODO: Calculate outstanding payments
        }
        return context

class CustomerCreateView(StaffRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'transport/customers/create.html'
    success_url = reverse_lazy('transport:customers-list')

    def form_valid(self, form):
        messages.success(self.request, f'Customer {form.instance.company_name} created successfully!')
        return super().form_valid(form)

class CustomerUpdateView(StaffRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'transport/customers/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:customer-detail', kwargs={'pk': self.object.pk})

# ============ ROUTE MANAGEMENT ============

class RouteListView(StaffRequiredMixin, ListView):
    model = Route
    template_name = 'transport/routes/list.html'
    context_object_name = 'routes'
    paginate_by = 20

    def get_queryset(self):
        queryset = Route.objects.all()
        search = self.request.GET.get('search')
        
        if search:
            queryset = queryset.filter(
                Q(origin__icontains=search) |
                Q(destination__icontains=search)
            )
        
        return queryset.order_by('origin', 'destination')

class RouteDetailView(StaffRequiredMixin, DetailView):
    model = Route
    template_name = 'transport/routes/detail.html'
    context_object_name = 'route'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route = self.get_object()
        context['recent_trips'] = Trip.objects.filter(route=route).order_by('-created_at')[:5]
        context['route_analytics'] = {
            'total_trips': Trip.objects.filter(route=route).count(),
            'avg_duration': 0,  # TODO: Calculate from trip data
            'profitability': 0,  # TODO: Calculate profit metrics
        }
        return context

class RouteCreateView(StaffRequiredMixin, CreateView):
    model = Route
    form_class = RouteForm
    template_name = 'transport/routes/create.html'
    success_url = reverse_lazy('transport:routes-list')

    def form_valid(self, form):
        messages.success(self.request, f'Route {form.instance.origin} → {form.instance.destination} created successfully!')
        return super().form_valid(form)

class RouteUpdateView(StaffRequiredMixin, UpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'transport/routes/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:route-detail', kwargs={'pk': self.object.pk})

# ============ TRIP MANAGEMENT ============

class TripListView(StaffRequiredMixin, ListView):
    model = Trip
    template_name = 'transport/trips/list.html'
    context_object_name = 'trips'
    paginate_by = 20

    def get_queryset(self):
        queryset = Trip.objects.select_related('vehicle', 'driver', 'customer', 'route').all()
        
        # Filtering
        status = self.request.GET.get('status')
        driver_id = self.request.GET.get('driver')
        vehicle_id = self.request.GET.get('vehicle')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__company_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')

class TripDetailView(StaffRequiredMixin, DetailView):
    model = Trip
    template_name = 'transport/trips/detail.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        
        # Add additional context for trip management
        context['can_start'] = trip.status == 'assigned'
        context['can_complete'] = trip.status == 'in_progress'
        context['can_cancel'] = trip.status in ['pending', 'assigned']
        
        return context

# ============ AJAX VIEWS FOR STATUS UPDATES ============

@login_required
def update_trip_status(request, trip_id):
    """AJAX view to update trip status"""
    if not request.user.role in ['superadmin', 'admin', 'manager', 'driver']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    trip = get_object_or_404(Trip, id=trip_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Trip.STATUS_CHOICES):
        trip.status = new_status
        trip.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Trip status updated to {trip.get_status_display()}'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})

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
