from django.urls import path

from .views import clients_summary

urlpatterns = [
    path("summary/", clients_summary, name="clients-summary"),
]
