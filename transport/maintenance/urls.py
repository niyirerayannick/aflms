from django.urls import path
from . import views

app_name = 'maintenance'

# Maintenance management endpoints
urlpatterns = [
    path("", views.MaintenanceListView.as_view(), name="list"),
    path("create/", views.MaintenanceCreateView.as_view(), name="create"),
    path("<int:pk>/", views.MaintenanceDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.MaintenanceUpdateView.as_view(), name="edit"),
]