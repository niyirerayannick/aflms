from django.urls import path
from . import views

app_name = 'fuel'

# Fuel management endpoints
urlpatterns = [
    path("", views.FuelEntryListView.as_view(), name="list"),
    path("create/", views.FuelEntryCreateView.as_view(), name="create"),
    path("<int:pk>/", views.FuelEntryDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.FuelEntryUpdateView.as_view(), name="edit"),

    # Fuel station management
    path("stations/", views.FuelStationListView.as_view(), name="station-list"),
    path("stations/create/", views.FuelStationCreateView.as_view(), name="station-create"),
    path("stations/<int:pk>/", views.FuelStationDetailView.as_view(), name="station-detail"),
    path("stations/<int:pk>/edit/", views.FuelStationUpdateView.as_view(), name="station-edit"),
    path("stations/<int:pk>/delete/", views.FuelStationDeleteView.as_view(), name="station-delete"),

    # Fuel intelligence endpoints
    path("analytics/", views.FuelAnalyticsDashboardView.as_view(), name="analytics"),
    path("efficiency/", views.FuelEfficiencyView.as_view(), name="efficiency"),
    path("trends/", views.MonthlyTrendView.as_view(), name="trends"),
    path("alerts/", views.FuelVarianceAlertsView.as_view(), name="alerts"),
]