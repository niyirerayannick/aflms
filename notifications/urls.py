from django.urls import path

from .views import notifications_summary

urlpatterns = [
    path("summary/", notifications_summary, name="notifications-summary"),
]
