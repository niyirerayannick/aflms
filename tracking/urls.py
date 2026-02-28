from django.urls import path

from .views import tracking_summary

urlpatterns = [
    path("summary/", tracking_summary, name="tracking-summary"),
]
