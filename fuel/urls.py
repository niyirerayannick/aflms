from django.urls import path

from .views import fuel_summary

urlpatterns = [
    path("summary/", fuel_summary, name="fuel-summary"),
]
