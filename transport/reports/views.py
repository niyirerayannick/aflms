from django.shortcuts import render, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, TemplateView
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import csv
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from transport.trips.models import Trip
from transport.vehicles.models import Vehicle
from transport.drivers.models import Driver
from transport.finance.models import Payment, Expense
from transport.maintenance.models import MaintenanceRecord


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access level"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['superadmin', 'admin', 'manager']


class ReportsDashboardView(StaffRequiredMixin, TemplateView):
    """Central reporting hub dashboard"""
    template_name = 'transport/reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Quick stats for dashboard
        total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'total_trips': Trip.objects.count(),
            'total_vehicles': Vehicle.objects.count(),
            'total_drivers': Driver.objects.count(),
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': total_revenue - total_expenses,
            'recent_trips': Trip.objects.select_related('customer', 'vehicle', 'driver').order_by('-created_at')[:5],
        })
        
        return context


class CustomReportView(StaffRequiredMixin, TemplateView):
    """Generate custom reports with flexible parameters"""
    template_name = 'transport/reports/custom.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Available report types
        context['report_types'] = [
            {'id': 'trips', 'name': 'Trip Reports', 'description': 'Detailed trip analysis and statistics'},
            {'id': 'financial', 'name': 'Financial Reports', 'description': 'Revenue, expenses, and profit analysis'},
            {'id': 'vehicles', 'name': 'Vehicle Reports', 'description': 'Vehicle performance and maintenance'},
            {'id': 'drivers', 'name': 'Driver Reports', 'description': 'Driver performance and activities'},
            {'id': 'customers', 'name': 'Customer Reports', 'description': 'Customer activity and revenue'},
        ]
        
        return context


class TripSummaryReportView(StaffRequiredMixin, TemplateView):
    """Comprehensive trip summary reports"""
    template_name = 'transport/reports/trip_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        trips = Trip.objects.all()
        
        if date_from:
            trips = trips.filter(created_at__gte=date_from)
        if date_to:
            trips = trips.filter(created_at__lte=date_to)
        
        # Trip statistics
        context.update({
            'trip_count': trips.count(),
            'completed_trips': trips.filter(status='completed').count(),
            'in_progress_trips': trips.filter(status='in_progress').count(),
            'cancelled_trips': trips.filter(status='cancelled').count(),
            'total_distance': trips.aggregate(Sum('distance_km'))['distance_km__sum'] or 0,
            'avg_distance': trips.aggregate(Avg('distance_km'))['distance_km__avg'] or 0,
            'trips_by_month': self.get_trips_by_month(trips),
            'trips_by_route': self.get_trips_by_route(trips),
            'date_from': date_from,
            'date_to': date_to,
        })
        
        return context

    def get_trips_by_month(self, queryset):
        """Get trip counts grouped by month"""
        from django.db.models import TruncMonth
        return list(queryset.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')[:12])

    def get_trips_by_route(self, queryset):
        """Get trip counts by route"""
        return list(queryset.values(
            'route__origin', 'route__destination'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10])


class DriverPerformanceReportView(StaffRequiredMixin, TemplateView):
    """Driver performance analysis"""
    template_name = 'transport/reports/driver_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Driver performance metrics
        driver_stats = []
        for driver in Driver.objects.all():
            trips = Trip.objects.filter(driver=driver)
            driver_stats.append({
                'driver': driver,
                'total_trips': trips.count(),
                'completed_trips': trips.filter(status='completed').count(),
                'total_distance': trips.aggregate(Sum('distance_km'))['distance_km__sum'] or 0,
                'completion_rate': (trips.filter(status='completed').count() / max(trips.count(), 1)) * 100,
            })
        
        context['driver_stats'] = sorted(driver_stats, key=lambda x: x['total_trips'], reverse=True)
        
        return context


class VehiclePerformanceReportView(StaffRequiredMixin, TemplateView):
    """Vehicle performance and maintenance reports"""
    template_name = 'transport/reports/vehicle_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Vehicle performance metrics
        vehicle_stats = []
        for vehicle in Vehicle.objects.all():
            trips = Trip.objects.filter(vehicle=vehicle)
            maintenance = MaintenanceRecord.objects.filter(vehicle=vehicle)
            
            vehicle_stats.append({
                'vehicle': vehicle,
                'total_trips': trips.count(),
                'total_distance': trips.aggregate(Sum('distance_km'))['distance_km__sum'] or 0,
                'maintenance_count': maintenance.count(),
                'maintenance_cost': maintenance.aggregate(Sum('cost'))['cost__sum'] or 0,
                'avg_distance_per_trip': trips.aggregate(Avg('distance_km'))['distance_km__avg'] or 0,
            })
        
        context['vehicle_stats'] = sorted(vehicle_stats, key=lambda x: x['total_distance'], reverse=True)
        
        return context


class FinancialSummaryReportView(StaffRequiredMixin, TemplateView):
    """Financial summary and analysis"""
    template_name = 'transport/reports/financial_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        payments = Payment.objects.all()
        expenses = Expense.objects.all()
        
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
            expenses = expenses.filter(expense_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)
            expenses = expenses.filter(expense_date__lte=date_to)
        
        total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': total_revenue - total_expenses,
            'payment_count': payments.count(),
            'expense_count': expenses.count(),
            'avg_payment': payments.aggregate(Avg('amount'))['amount__avg'] or 0,
            'avg_expense': expenses.aggregate(Avg('amount'))['amount__avg'] or 0,
            'expenses_by_category': self.get_expenses_by_category(expenses),
            'revenue_by_month': self.get_revenue_by_month(payments),
            'date_from': date_from,
            'date_to': date_to,
        })
        
        return context

    def get_expenses_by_category(self, queryset):
        """Get expenses grouped by category"""
        return list(queryset.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total'))

    def get_revenue_by_month(self, queryset):
        """Get revenue grouped by month"""
        from django.db.models import TruncMonth
        return list(queryset.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')[:12])


class ExportExcelView(StaffRequiredMixin, TemplateView):
    """Export reports to Excel format"""
    template_name = 'transport/reports/export_excel.html'

    def post(self, request, *args, **kwargs):
        """Handle Excel export"""
        report_type = request.POST.get('report_type')
        
        if report_type == 'trips':
            return self.export_trips_excel()
        elif report_type == 'financial':
            return self.export_financial_excel()
        elif report_type == 'vehicles':
            return self.export_vehicles_excel()
        elif report_type == 'drivers':
            return self.export_drivers_excel()
        
        return JsonResponse({'error': 'Invalid report type'}, status=400)

    def export_trips_excel(self):
        """Export trips to Excel"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="trips_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Customer', 'Driver', 'Vehicle', 'Origin', 'Destination', 'Distance (km)', 'Status', 'Created At'])
        
        for trip in Trip.objects.select_related('customer', 'driver', 'vehicle', 'route').all():
            writer.writerow([
                trip.order_number,
                trip.customer.company_name if trip.customer else '',
                trip.driver.name if trip.driver else '',
                trip.vehicle.plate_number if trip.vehicle else '',
                trip.route.origin if trip.route else '',
                trip.route.destination if trip.route else '',
                trip.distance,
                trip.get_status_display(),
                trip.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        
        return response

    def export_financial_excel(self):
        """Export financial data to Excel"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Type', 'Date', 'Amount', 'Reference', 'Description', 'Category'])
        
        # Add payments
        for payment in Payment.objects.all():
            writer.writerow([
                'Revenue',
                payment.payment_date,
                payment.amount,
                payment.reference,
                f"Payment for trip {payment.trip.order_number}" if payment.trip else '',
                'Payment'
            ])
        
        # Add expenses
        for expense in Expense.objects.all():
            writer.writerow([
                'Expense',
                expense.expense_date,
                expense.amount,
                expense.reference,
                expense.description,
                expense.category
            ])
        
        return response


class ExportPDFView(StaffRequiredMixin, TemplateView):
    """Export reports to PDF format"""
    template_name = 'transport/reports/export_pdf.html'

    def post(self, request, *args, **kwargs):
        """Handle PDF export"""
        report_type = request.POST.get('report_type')
        
        if report_type == 'trips':
            return self.export_trips_pdf()
        elif report_type == 'financial':
            return self.export_financial_pdf()
        
        return JsonResponse({'error': 'Invalid report type'}, status=400)

    def export_trips_pdf(self):
        """Export trips summary to PDF"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, "Trip Summary Report")
        
        # Generate date
        p.setFont("Helvetica", 12)
        p.drawString(50, 720, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Statistics
        y_position = 680
        stats = [
            f"Total Trips: {Trip.objects.count()}",
            f"Completed Trips: {Trip.objects.filter(status='completed').count()}",
            f"In Progress: {Trip.objects.filter(status='in_progress').count()}",
            f"Total Distance: {Trip.objects.aggregate(Sum('distance_km'))['distance_km__sum'] or 0} km",
        ]
        
        for stat in stats:
            p.drawString(50, y_position, stat)
            y_position -= 20
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="trips_report.pdf"'
        
        return response