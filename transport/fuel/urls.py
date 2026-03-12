from django.urls import path
from . import views

app_name = 'fuel'

urlpatterns = [
    path("", views.FuelRequestListView.as_view(), name="list"),
    path("analytics/", views.FuelRequestAnalyticsView.as_view(), name="analytics"),
    path("<int:pk>/", views.FuelRequestDetailView.as_view(), name="detail"),
    path("<int:pk>/approve/", views.approve_fuel_request, name="approve"),
    path("request/", views.request_fuel, name="request"),
    path("request/<int:fuel_request_id>/upload/", views.upload_fuel_document, name="upload_document"),
]
