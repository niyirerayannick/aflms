from django.urls import path

from .views import (
    ReportsDashboardView,
    CustomReportView,
    TripSummaryReportView,
    DriverPerformanceReportView,
    VehiclePerformanceReportView,
    FinancialSummaryReportView,
    ExportExcelView,
    ExportPDFView,
)

app_name = "reports"

urlpatterns = [
    # Main reports dashboard
    path("", ReportsDashboardView.as_view(), name="dashboard"),
    
    # Custom reports
    path("custom/", CustomReportView.as_view(), name="custom"),
    
    # Specific reports
    path("trips/", TripSummaryReportView.as_view(), name="trip-summary"),
    path("drivers/", DriverPerformanceReportView.as_view(), name="driver-performance"),
    path("vehicles/", VehiclePerformanceReportView.as_view(), name="vehicle-performance"),
    path("financial/", FinancialSummaryReportView.as_view(), name="financial-summary"),
    
    # Export functionality
    path("export/excel/", ExportExcelView.as_view(), name="export-excel"),
    path("export/pdf/", ExportPDFView.as_view(), name="export-pdf"),
]