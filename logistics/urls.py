from django.urls import path

from .views import logistics_summary

urlpatterns = [
    path("summary/", logistics_summary, name="logistics-summary"),
]
