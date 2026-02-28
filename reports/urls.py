from django.urls import path

from .views import reports_summary

urlpatterns = [
    path("summary/", reports_summary, name="reports-summary"),
]
