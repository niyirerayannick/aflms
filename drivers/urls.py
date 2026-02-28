from django.urls import path

from .views import drivers_summary

urlpatterns = [
    path("summary/", drivers_summary, name="drivers-summary"),
]
