# Route Module Views
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from django.utils.decorators import method_decorator

from .models import Route
from .forms import RouteForm
from transport.trips.models import Trip

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Route statistics
        all_routes = Route.objects.all()
        context['total_routes'] = all_routes.count()
        context['active_routes'] = all_routes.filter(is_active=True).count()
        context['total_distance'] = all_routes.aggregate(total=Sum('distance_km'))['total'] or 0
        context['avg_distance'] = all_routes.aggregate(avg_dist=Avg('distance_km'))['avg_dist'] or 0
        
        return context

class RouteDetailView(StaffRequiredMixin, DetailView):
    model = Route
    template_name = 'transport/routes/detail.html'
    context_object_name = 'route'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route = self.get_object()
        
        # Add tabs data
        tab = self.request.GET.get('tab', 'overview')
        context['current_tab'] = tab
        
        # Recent trips on this route
        context['recent_trips'] = Trip.objects.filter(
            route=route
        ).select_related('customer', 'vehicle', 'driver').order_by('-created_at')[:10]
        
        # Route performance metrics
        route_trips = Trip.objects.filter(route=route)
        completed_trips = route_trips.filter(status__in=['DELIVERED', 'CLOSED'])
        
        context['route_analytics'] = {
            'total_trips': route_trips.count(),
            'completed_trips': completed_trips.count(),
            'total_revenue': completed_trips.aggregate(total=Sum('revenue'))['total'] or 0,
            'avg_trip_duration': '4h 30m',  # TODO: Calculate from trip data
            'utilization_rate': 78,  # TODO: Calculate utilization
            'profitability_score': 85,  # TODO: Calculate profit metrics
        }
        
        return context

class RouteCreateView(StaffRequiredMixin, CreateView):
    model = Route
    form_class = RouteForm
    template_name = 'transport/routes/create.html'
    success_url = reverse_lazy('transport:routes:list')

    def form_valid(self, form):
        messages.success(self.request, f'Route {form.instance.origin} → {form.instance.destination} created successfully!')
        return super().form_valid(form)

class RouteUpdateView(StaffRequiredMixin, UpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'transport/routes/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:routes:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Route updated successfully!')
        return super().form_valid(form)