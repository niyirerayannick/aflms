from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from transport.analytics.services import executive_dashboard_metrics, full_dashboard_context
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver
from transport.trips.models import Trip


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensures user is staff (admin, manager, or superadmin)"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in [
            'superadmin', 'admin', 'manager'
        ]


@login_required
def dashboard_view(request):
    """Main ATMS dashboard showing key metrics and recent activity"""
    if request.user.role not in ['superadmin', 'admin', 'manager']:
        return render(request, 'transport/access_denied.html')
    
    context = full_dashboard_context()
    context['page_title'] = 'System Overview'
    
    return render(request, 'transport/dashboard.html', context)


@login_required
def dashboard_api(request):
    """API endpoint for dashboard metrics (for AJAX updates)"""
    if request.user.role not in ['superadmin', 'admin', 'manager']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    metrics = executive_dashboard_metrics()
    
    # Convert Decimal to string for JSON serialization
    for key, value in metrics.items():
        if hasattr(value, 'quantize'):  # Decimal type
            metrics[key] = str(value)
    
    return JsonResponse(metrics)


class VehicleListView(StaffRequiredMixin, ListView):
    """List all vehicles with filtering and search"""
    model = Vehicle
    template_name = 'transport/vehicles/list.html'
    context_object_name = 'vehicles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Vehicle.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(plate_number__icontains=search)
        
        # Status filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('plate_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Fleet Management'
        context['status_choices'] = Vehicle.VehicleStatus.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class TripListView(ListView):
    """List trips based on user role"""
    model = Trip
    template_name = 'transport/trips/list.html'
    context_object_name = 'trips'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Trip.objects.select_related('customer', 'vehicle', 'driver', 'route')
        
        # Filter based on user role
        if user.role == 'driver':
            # Drivers see only their assigned trips
            try:
                driver = Driver.objects.get(user=user)
                queryset = queryset.filter(driver=driver)
            except Driver.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'client':
            # Clients see only their trips
            try:
                # Assuming customer is linked to user somehow
                queryset = queryset.filter(customer__user=user)
            except:
                queryset = queryset.none()
        # Staff roles see all trips
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(order_number__icontains=search)
        
        # Status filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Trips Management'
        context['status_choices'] = Trip.TripStatus.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class TripDetailView(DetailView):
    """Detailed view of a trip"""
    model = Trip
    template_name = 'transport/trips/detail.html'
    context_object_name = 'trip'
    
    def get_queryset(self):
        user = self.request.user
        queryset = Trip.objects.select_related('customer', 'vehicle', 'driver', 'route')
        
        # Apply same filtering as list view
        if user.role == 'driver':
            try:
                driver = Driver.objects.get(user=user)
                queryset = queryset.filter(driver=driver)
            except Driver.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'client':
            try:
                queryset = queryset.filter(customer__user=user)
            except:
                queryset = queryset.none()
        
        return queryset


@login_required 
def driver_dashboard(request):
    """Dashboard specifically for drivers"""
    if request.user.role != 'driver':
        return render(request, 'transport/access_denied.html')
    
    try:
        driver = Driver.objects.get(user=request.user)
        active_trips = Trip.objects.filter(
            driver=driver, 
            status__in=[Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT]
        ).select_related('customer', 'route')
        
        recent_trips = Trip.objects.filter(driver=driver).order_by('-created_at')[:10]
        
        context = {
            'driver': driver,
            'active_trips': active_trips,
            'recent_trips': recent_trips,
            'page_title': 'Driver Dashboard'
        }
        
        return render(request, 'transport/driver_dashboard.html', context)
        
    except Driver.DoesNotExist:
        return render(request, 'transport/access_denied.html', {
            'message': 'Driver profile not found. Please contact administrator.'
        })


@login_required
def client_dashboard(request):
    """Dashboard for clients/customers"""
    if request.user.role != 'client':
        return render(request, 'transport/access_denied.html')
    
    # Get customer's trips
    customer_trips = Trip.objects.filter(
        # customer__user=request.user  # Uncomment when Customer model has user field
    ).order_by('-created_at')[:20]
    
    active_orders = customer_trips.filter(
        status__in=[Trip.TripStatus.APPROVED, Trip.TripStatus.ASSIGNED, Trip.TripStatus.IN_TRANSIT]
    )
    
    context = {
        'customer_trips': customer_trips,
        'active_orders': active_orders,
        'page_title': 'My Orders'
    }
    
    return render(request, 'transport/client_dashboard.html', context)


# Legacy API endpoint for compatibility
def executive_dashboard_api(_request):
    return JsonResponse(executive_dashboard_metrics())
