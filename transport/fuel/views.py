# Fuel Intelligence Module Views
import json
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count, F, Min, Max, StdDev
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils.decorators import method_decorator
from django.utils import timezone

from .models import FuelEntry, FuelStation
from .forms import FuelEntryForm, FuelStationForm

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']

class FuelEntryListView(StaffRequiredMixin, ListView):
    model = FuelEntry
    template_name = 'transport/fuel/list.html'
    context_object_name = 'fuel_entries'
    paginate_by = 20

    def get_queryset(self):
        queryset = FuelEntry.objects.select_related('trip', 'station').all()
        search = self.request.GET.get('search')
        station = self.request.GET.get('station')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(trip__order_number__icontains=search) |
                Q(fuel_station__icontains=search) |
                Q(station__name__icontains=search)
            )
        
        if station:
            queryset = queryset.filter(station_id=station)
            
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
            
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.order_by('-date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fuel statistics
        all_entries = FuelEntry.objects.all()
        context['total_entries'] = all_entries.count()
        context['total_liters'] = all_entries.aggregate(total=Sum('liters'))['total'] or 0
        context['total_cost'] = all_entries.aggregate(total=Sum('total_cost'))['total'] or 0
        context['avg_price_per_liter'] = all_entries.aggregate(avg=Avg('price_per_liter'))['avg'] or 0
        
        # Top fuel stations
        context['top_stations'] = FuelEntry.objects.values('station__name').annotate(
            total_cost=Sum('total_cost'),
            total_liters=Sum('liters')
        ).order_by('-total_cost')[:5]
        
        return context

class FuelEntryDetailView(StaffRequiredMixin, DetailView):
    model = FuelEntry
    template_name = 'transport/fuel/detail.html'
    context_object_name = 'fuel_entry'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'station', 'trip__vehicle', 'trip__driver', 'trip__route', 'trip__customer'
        )

class FuelEntryCreateView(StaffRequiredMixin, CreateView):
    model = FuelEntry
    form_class = FuelEntryForm
    template_name = 'transport/fuel/create.html'
    success_url = reverse_lazy('transport:fuel:list')

    def form_valid(self, form):
        messages.success(self.request, 'Fuel entry created successfully!')
        return super().form_valid(form)

class FuelEntryUpdateView(StaffRequiredMixin, UpdateView):
    model = FuelEntry
    form_class = FuelEntryForm
    template_name = 'transport/fuel/edit.html'
    
    def get_success_url(self):
        return reverse_lazy('transport:fuel:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Fuel entry updated successfully!')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Fuel Station CRUD
# ---------------------------------------------------------------------------

class FuelStationListView(StaffRequiredMixin, ListView):
    model = FuelStation
    template_name = 'transport/fuel/stations/list.html'
    context_object_name = 'stations'
    paginate_by = 25

    def get_queryset(self):
        qs = FuelStation.objects.annotate(
            entry_count=Count('fuel_entries'),
            total_liters=Sum('fuel_entries__liters'),
            total_cost=Sum('fuel_entries__total_cost'),
        )
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(location__icontains=search))
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_stations'] = FuelStation.objects.count()
        ctx['active_stations'] = FuelStation.objects.filter(is_active=True).count()
        ctx['inactive_stations'] = FuelStation.objects.filter(is_active=False).count()
        ctx['search_query'] = self.request.GET.get('search', '')
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class FuelStationDetailView(StaffRequiredMixin, DetailView):
    model = FuelStation
    template_name = 'transport/fuel/stations/detail.html'
    context_object_name = 'station'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        station = self.get_object()
        entries = FuelEntry.objects.filter(station=station).select_related('trip')
        ctx['recent_entries'] = entries.order_by('-date')[:10]
        agg = entries.aggregate(
            total_liters=Sum('liters'),
            total_cost=Sum('total_cost'),
            avg_price=Avg('price_per_liter'),
            entry_count=Count('id'),
        )
        ctx['total_liters'] = agg['total_liters'] or 0
        ctx['total_cost'] = agg['total_cost'] or 0
        ctx['avg_price'] = agg['avg_price'] or 0
        ctx['entry_count'] = agg['entry_count'] or 0
        return ctx


class FuelStationCreateView(StaffRequiredMixin, CreateView):
    model = FuelStation
    form_class = FuelStationForm
    template_name = 'transport/fuel/stations/create.html'
    success_url = reverse_lazy('transport:fuel:station-list')

    def form_valid(self, form):
        messages.success(self.request, f'Fuel station "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class FuelStationUpdateView(StaffRequiredMixin, UpdateView):
    model = FuelStation
    form_class = FuelStationForm
    template_name = 'transport/fuel/stations/edit.html'

    def get_success_url(self):
        return reverse_lazy('transport:fuel:station-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Fuel station "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class FuelStationDeleteView(StaffRequiredMixin, DeleteView):
    model = FuelStation
    template_name = 'transport/fuel/stations/delete.html'
    success_url = reverse_lazy('transport:fuel:station-list')

    def form_valid(self, form):
        messages.success(self.request, f'Fuel station "{self.object.name}" deleted.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Fuel Analytics Dashboard
# ---------------------------------------------------------------------------
class FuelAnalyticsDashboardView(StaffRequiredMixin, TemplateView):
    """Comprehensive fuel analytics dashboard with KPI cards, charts data, and breakdowns."""
    template_name = 'transport/fuel/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = FuelEntry.objects.select_related('trip', 'trip__vehicle', 'trip__driver').all()

        # ---- KPI summary -------------------------------------------------
        agg = entries.aggregate(
            total_entries=Count('id'),
            total_liters=Sum('liters'),
            total_cost=Sum('total_cost'),
            avg_price=Avg('price_per_liter'),
            min_price=Min('price_per_liter'),
            max_price=Max('price_per_liter'),
        )
        context['total_entries'] = agg['total_entries'] or 0
        context['total_liters'] = agg['total_liters'] or Decimal('0')
        context['total_cost'] = agg['total_cost'] or Decimal('0')
        context['avg_price'] = agg['avg_price'] or Decimal('0')
        context['min_price'] = agg['min_price'] or Decimal('0')
        context['max_price'] = agg['max_price'] or Decimal('0')

        # Average cost per entry
        if agg['total_entries']:
            context['avg_cost_per_entry'] = (agg['total_cost'] or Decimal('0')) / agg['total_entries']
        else:
            context['avg_cost_per_entry'] = Decimal('0')

        # Fleet-wide efficiency (total distance / total liters)
        from transport.trips.models import Trip
        trip_ids = entries.values_list('trip_id', flat=True).distinct()
        distance_agg = Trip.objects.filter(id__in=trip_ids).aggregate(total_distance=Sum('distance'))
        total_distance = distance_agg['total_distance'] or Decimal('0')
        context['total_distance'] = total_distance
        if agg['total_liters'] and agg['total_liters'] > 0:
            context['fleet_efficiency'] = round(total_distance / agg['total_liters'], 2)
            context['cost_per_km'] = round((agg['total_cost'] or Decimal('0')) / total_distance, 2) if total_distance > 0 else Decimal('0')
        else:
            context['fleet_efficiency'] = Decimal('0')
            context['cost_per_km'] = Decimal('0')

        # ---- Monthly trend (last 12 months) for chart --------------------
        twelve_months_ago = timezone.now().date().replace(day=1) - timedelta(days=365)
        monthly = (
            entries.filter(date__gte=twelve_months_ago)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                liters=Sum('liters'),
                cost=Sum('total_cost'),
                count=Count('id'),
                avg_price=Avg('price_per_liter'),
            )
            .order_by('month')
        )
        context['monthly_labels'] = json.dumps([m['month'].strftime('%b %Y') for m in monthly])
        context['monthly_liters'] = json.dumps([float(m['liters'] or 0) for m in monthly])
        context['monthly_cost'] = json.dumps([float(m['cost'] or 0) for m in monthly])
        context['monthly_count'] = json.dumps([m['count'] for m in monthly])

        # ---- Consumption by vehicle type ---------------------------------
        by_vtype = (
            entries.values('trip__vehicle__vehicle_type')
            .annotate(liters=Sum('liters'), cost=Sum('total_cost'), count=Count('id'))
            .order_by('-liters')
        )
        context['vtype_labels'] = json.dumps([v['trip__vehicle__vehicle_type'] or 'Unknown' for v in by_vtype])
        context['vtype_liters'] = json.dumps([float(v['liters'] or 0) for v in by_vtype])
        context['vtype_cost'] = json.dumps([float(v['cost'] or 0) for v in by_vtype])

        # ---- Top 10 stations by cost ------------------------------------
        top_stations = (
            entries.values('station__name')
            .annotate(cost=Sum('total_cost'), liters=Sum('liters'), count=Count('id'), avg_price=Avg('price_per_liter'))
            .order_by('-cost')[:10]
        )
        context['top_stations'] = top_stations
        context['station_labels'] = json.dumps([s['station__name'] or 'Unknown' for s in top_stations])
        context['station_cost'] = json.dumps([float(s['cost'] or 0) for s in top_stations])

        # ---- Top 10 consuming vehicles -----------------------------------
        top_vehicles = (
            entries.values('trip__vehicle__plate_number', 'trip__vehicle__vehicle_type')
            .annotate(liters=Sum('liters'), cost=Sum('total_cost'), count=Count('id'))
            .order_by('-liters')[:10]
        )
        context['top_vehicles'] = top_vehicles

        # ---- Recent entries (last 5) ------------------------------------
        context['recent_entries'] = entries.order_by('-date', '-created_at')[:5]

        return context


# ---------------------------------------------------------------------------
# Fuel Efficiency per Vehicle
# ---------------------------------------------------------------------------
class FuelEfficiencyView(StaffRequiredMixin, TemplateView):
    """Per-vehicle fuel efficiency analysis – km/L, cost/km, ranking."""
    template_name = 'transport/fuel/efficiency.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from transport.trips.models import Trip
        from transport.vehicles.models import Vehicle

        # Filter params
        vehicle_type = self.request.GET.get('vehicle_type', '')
        sort_by = self.request.GET.get('sort', 'efficiency')  # efficiency | cost_per_km | liters | cost

        entries = FuelEntry.objects.select_related('trip__vehicle')

        # Build per-vehicle aggregation
        vehicle_data = (
            entries.values(
                'trip__vehicle__id',
                'trip__vehicle__plate_number',
                'trip__vehicle__vehicle_type',
                'trip__vehicle__current_odometer',
            )
            .annotate(
                total_liters=Sum('liters'),
                total_cost=Sum('total_cost'),
                entry_count=Count('id'),
                avg_price=Avg('price_per_liter'),
                first_entry=Min('date'),
                last_entry=Max('date'),
            )
        )

        if vehicle_type:
            vehicle_data = vehicle_data.filter(trip__vehicle__vehicle_type=vehicle_type)

        # Enrich with distance data and efficiency
        vehicles = []
        for v in vehicle_data:
            vid = v['trip__vehicle__id']
            if not vid:
                continue
            trip_agg = Trip.objects.filter(vehicle_id=vid).aggregate(
                total_distance=Sum('distance'),
                trip_count=Count('id'),
            )
            total_distance = trip_agg['total_distance'] or Decimal('0')
            total_liters = v['total_liters'] or Decimal('0')
            total_cost = v['total_cost'] or Decimal('0')

            efficiency = round(total_distance / total_liters, 2) if total_liters > 0 else Decimal('0')
            cpk = round(total_cost / total_distance, 2) if total_distance > 0 else Decimal('0')
            cpl = round(total_cost / total_liters, 2) if total_liters > 0 else Decimal('0')

            vehicles.append({
                'plate_number': v['trip__vehicle__plate_number'],
                'vehicle_type': v['trip__vehicle__vehicle_type'],
                'odometer': v['trip__vehicle__current_odometer'],
                'total_liters': total_liters,
                'total_cost': total_cost,
                'total_distance': total_distance,
                'trip_count': trip_agg['trip_count'] or 0,
                'entry_count': v['entry_count'],
                'avg_price': v['avg_price'] or Decimal('0'),
                'efficiency': efficiency,
                'cost_per_km': cpk,
                'cost_per_liter': cpl,
                'first_entry': v['first_entry'],
                'last_entry': v['last_entry'],
            })

        # Sort
        sort_map = {
            'efficiency': lambda x: x['efficiency'],
            'cost_per_km': lambda x: x['cost_per_km'],
            'liters': lambda x: x['total_liters'],
            'cost': lambda x: x['total_cost'],
            'plate': lambda x: x['plate_number'] or '',
        }
        sort_fn = sort_map.get(sort_by, sort_map['efficiency'])
        reverse = sort_by != 'plate'
        vehicles.sort(key=sort_fn, reverse=reverse)

        # Fleet averages
        if vehicles:
            eff_values = [v['efficiency'] for v in vehicles if v['efficiency'] > 0]
            cpk_values = [v['cost_per_km'] for v in vehicles if v['cost_per_km'] > 0]
            context['fleet_avg_efficiency'] = round(sum(eff_values) / len(eff_values), 2) if eff_values else Decimal('0')
            context['fleet_avg_cpk'] = round(sum(cpk_values) / len(cpk_values), 2) if cpk_values else Decimal('0')
            # Best / worst
            eff_sorted = sorted([v for v in vehicles if v['efficiency'] > 0], key=lambda x: x['efficiency'], reverse=True)
            context['best_vehicle'] = eff_sorted[0] if eff_sorted else None
            context['worst_vehicle'] = eff_sorted[-1] if len(eff_sorted) > 1 else None
        else:
            context['fleet_avg_efficiency'] = Decimal('0')
            context['fleet_avg_cpk'] = Decimal('0')
            context['best_vehicle'] = None
            context['worst_vehicle'] = None

        # Chart data – efficiency ranking
        context['chart_labels'] = json.dumps([v['plate_number'] for v in vehicles[:15]])
        context['chart_efficiency'] = json.dumps([float(v['efficiency']) for v in vehicles[:15]])
        context['chart_cpk'] = json.dumps([float(v['cost_per_km']) for v in vehicles[:15]])

        # Vehicle types for filter dropdown
        context['vehicle_types'] = Vehicle.VEHICLE_TYPE_CHOICES
        context['selected_type'] = vehicle_type
        context['selected_sort'] = sort_by
        context['vehicles'] = vehicles
        context['vehicle_count'] = len(vehicles)

        return context


# ---------------------------------------------------------------------------
# Monthly Fuel Trends
# ---------------------------------------------------------------------------
class MonthlyTrendView(StaffRequiredMixin, TemplateView):
    """Month-over-month fuel consumption and cost trends with comparisons."""
    template_name = 'transport/fuel/trends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Year filter
        year_param = self.request.GET.get('year', '')
        available_years = (
            FuelEntry.objects.dates('date', 'year', order='DESC')
        )
        context['available_years'] = [d.year for d in available_years]
        context['selected_year'] = int(year_param) if year_param.isdigit() else None

        entries = FuelEntry.objects.select_related('trip', 'trip__vehicle')
        if context['selected_year']:
            entries = entries.filter(date__year=context['selected_year'])

        # Monthly aggregation
        monthly = (
            entries.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                liters=Sum('liters'),
                cost=Sum('total_cost'),
                count=Count('id'),
                avg_price=Avg('price_per_liter'),
                min_price=Min('price_per_liter'),
                max_price=Max('price_per_liter'),
                stations=Count('fuel_station', distinct=True),
            )
            .order_by('month')
        )

        months_data = []
        prev_liters = None
        prev_cost = None
        for m in monthly:
            liters = m['liters'] or Decimal('0')
            cost = m['cost'] or Decimal('0')
            liters_change = None
            cost_change = None
            if prev_liters is not None and prev_liters > 0:
                liters_change = round(((liters - prev_liters) / prev_liters) * 100, 1)
            if prev_cost is not None and prev_cost > 0:
                cost_change = round(((cost - prev_cost) / prev_cost) * 100, 1)

            months_data.append({
                'month': m['month'],
                'month_label': m['month'].strftime('%B %Y'),
                'month_short': m['month'].strftime('%b %Y'),
                'liters': liters,
                'cost': cost,
                'count': m['count'],
                'avg_price': m['avg_price'] or Decimal('0'),
                'min_price': m['min_price'] or Decimal('0'),
                'max_price': m['max_price'] or Decimal('0'),
                'stations': m['stations'],
                'liters_change': liters_change,
                'cost_change': cost_change,
                'avg_cost_per_entry': round(cost / m['count'], 2) if m['count'] else Decimal('0'),
            })
            prev_liters = liters
            prev_cost = cost

        context['months_data'] = months_data

        # Chart data
        context['chart_labels'] = json.dumps([m['month_short'] for m in months_data])
        context['chart_liters'] = json.dumps([float(m['liters']) for m in months_data])
        context['chart_cost'] = json.dumps([float(m['cost']) for m in months_data])
        context['chart_avg_price'] = json.dumps([float(m['avg_price']) for m in months_data])
        context['chart_count'] = json.dumps([m['count'] for m in months_data])

        # Summary stats
        if months_data:
            context['peak_month'] = max(months_data, key=lambda x: x['liters'])
            context['lowest_month'] = min(months_data, key=lambda x: x['liters'])
            context['highest_cost_month'] = max(months_data, key=lambda x: x['cost'])
            total_liters = sum(m['liters'] for m in months_data)
            total_cost = sum(m['cost'] for m in months_data)
            context['grand_total_liters'] = total_liters
            context['grand_total_cost'] = total_cost
            context['monthly_avg_liters'] = round(total_liters / len(months_data), 1)
            context['monthly_avg_cost'] = round(total_cost / len(months_data), 2)
        else:
            context['peak_month'] = None
            context['lowest_month'] = None
            context['highest_cost_month'] = None
            context['grand_total_liters'] = Decimal('0')
            context['grand_total_cost'] = Decimal('0')
            context['monthly_avg_liters'] = Decimal('0')
            context['monthly_avg_cost'] = Decimal('0')

        # Weekly trend (last 12 weeks) for secondary chart
        twelve_weeks_ago = timezone.now().date() - timedelta(weeks=12)
        weekly = (
            FuelEntry.objects.filter(date__gte=twelve_weeks_ago)
            .annotate(week=TruncWeek('date'))
            .values('week')
            .annotate(liters=Sum('liters'), cost=Sum('total_cost'), count=Count('id'))
            .order_by('week')
        )
        context['weekly_labels'] = json.dumps([w['week'].strftime('%d %b') for w in weekly])
        context['weekly_liters'] = json.dumps([float(w['liters'] or 0) for w in weekly])
        context['weekly_cost'] = json.dumps([float(w['cost'] or 0) for w in weekly])

        return context


# ---------------------------------------------------------------------------
# Fuel Variance Alerts
# ---------------------------------------------------------------------------
class FuelVarianceAlertsView(StaffRequiredMixin, TemplateView):
    """Detect fuel consumption anomalies and cost variances across the fleet."""
    template_name = 'transport/fuel/alerts.html'

    # Thresholds (configurable via GET params)
    DEFAULT_PRICE_THRESHOLD = 20   # % above average price → flag
    DEFAULT_VOLUME_THRESHOLD = 50  # % above vehicle average consumption → flag
    DEFAULT_COST_THRESHOLD = 40    # % above average trip cost → flag

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from transport.trips.models import Trip

        price_threshold = int(self.request.GET.get('price_threshold', self.DEFAULT_PRICE_THRESHOLD))
        volume_threshold = int(self.request.GET.get('volume_threshold', self.DEFAULT_VOLUME_THRESHOLD))
        cost_threshold = int(self.request.GET.get('cost_threshold', self.DEFAULT_COST_THRESHOLD))

        context['price_threshold'] = price_threshold
        context['volume_threshold'] = volume_threshold
        context['cost_threshold'] = cost_threshold

        entries = FuelEntry.objects.select_related('trip', 'trip__vehicle', 'trip__driver').all()

        # Global averages
        global_avg = entries.aggregate(
            avg_price=Avg('price_per_liter'),
            avg_liters=Avg('liters'),
            avg_cost=Avg('total_cost'),
        )
        global_avg_price = global_avg['avg_price'] or Decimal('0')
        global_avg_liters = global_avg['avg_liters'] or Decimal('0')
        global_avg_cost = global_avg['avg_cost'] or Decimal('0')

        context['global_avg_price'] = global_avg_price
        context['global_avg_liters'] = global_avg_liters
        context['global_avg_cost'] = global_avg_cost

        # ---- Per-vehicle averages (for volume anomaly detection) ----------
        vehicle_avgs = {}
        veh_agg = (
            entries.values('trip__vehicle__id', 'trip__vehicle__plate_number')
            .annotate(avg_liters=Avg('liters'), avg_cost=Avg('total_cost'))
        )
        for va in veh_agg:
            vid = va['trip__vehicle__id']
            if vid:
                vehicle_avgs[vid] = {
                    'plate': va['trip__vehicle__plate_number'],
                    'avg_liters': va['avg_liters'] or Decimal('0'),
                    'avg_cost': va['avg_cost'] or Decimal('0'),
                }

        # ---- Scan all entries for anomalies ------------------------------
        price_alerts = []
        volume_alerts = []
        cost_alerts = []

        for entry in entries.order_by('-date')[:500]:  # Cap to recent 500
            # Price anomaly
            if global_avg_price > 0:
                price_dev = ((entry.price_per_liter - global_avg_price) / global_avg_price) * 100
                if price_dev > price_threshold:
                    price_alerts.append({
                        'entry': entry,
                        'deviation': round(price_dev, 1),
                        'expected': global_avg_price,
                        'actual': entry.price_per_liter,
                        'type': 'price',
                        'severity': 'high' if price_dev > price_threshold * 2 else 'medium',
                    })

            # Volume anomaly (per-vehicle basis)
            vid = entry.trip.vehicle_id if entry.trip and entry.trip.vehicle_id else None
            if vid and vid in vehicle_avgs:
                veh_avg = vehicle_avgs[vid]['avg_liters']
                if veh_avg > 0:
                    vol_dev = ((entry.liters - veh_avg) / veh_avg) * 100
                    if vol_dev > volume_threshold:
                        volume_alerts.append({
                            'entry': entry,
                            'deviation': round(vol_dev, 1),
                            'expected': round(veh_avg, 1),
                            'actual': entry.liters,
                            'vehicle': vehicle_avgs[vid]['plate'],
                            'type': 'volume',
                            'severity': 'high' if vol_dev > volume_threshold * 2 else 'medium',
                        })

            # Cost anomaly
            if global_avg_cost > 0:
                cost_dev = ((entry.total_cost - global_avg_cost) / global_avg_cost) * 100
                if cost_dev > cost_threshold:
                    cost_alerts.append({
                        'entry': entry,
                        'deviation': round(cost_dev, 1),
                        'expected': global_avg_cost,
                        'actual': entry.total_cost,
                        'type': 'cost',
                        'severity': 'high' if cost_dev > cost_threshold * 2 else 'medium',
                    })

        context['price_alerts'] = price_alerts[:50]
        context['volume_alerts'] = volume_alerts[:50]
        context['cost_alerts'] = cost_alerts[:50]
        context['total_alerts'] = len(price_alerts) + len(volume_alerts) + len(cost_alerts)
        context['high_severity_count'] = sum(
            1 for a in price_alerts + volume_alerts + cost_alerts if a['severity'] == 'high'
        )

        # ---- Station price comparison ------------------------------------
        station_prices = (
            entries.values('fuel_station')
            .annotate(
                avg_price=Avg('price_per_liter'),
                min_price=Min('price_per_liter'),
                max_price=Max('price_per_liter'),
                spread=Max('price_per_liter') - Min('price_per_liter'),
                count=Count('id'),
                total_cost=Sum('total_cost'),
            )
            .order_by('-avg_price')
        )
        context['station_prices'] = station_prices

        # Station with highest avg price vs lowest
        stations_list = list(station_prices)
        if stations_list:
            context['most_expensive_station'] = stations_list[0]
            context['cheapest_station'] = min(stations_list, key=lambda s: s['avg_price'])
        else:
            context['most_expensive_station'] = None
            context['cheapest_station'] = None

        return context