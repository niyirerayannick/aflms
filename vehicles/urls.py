from django.urls import path

from .views import vehicles_summary

urlpatterns = [
    path("summary/", vehicles_summary, name="vehicles-summary"),
]
