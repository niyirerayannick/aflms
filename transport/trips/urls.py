from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    path("", views.TripListView.as_view(), name="list"),
    path("create/", views.TripCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TripDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.TripUpdateView.as_view(), name="edit"),
    path("<int:trip_id>/status/", views.update_trip_status, name="status-update"),
    path("<int:trip_id>/accept/", views.accept_trip, name="accept"),
    path("<int:trip_id>/reject/", views.reject_trip, name="reject"),
    path("<int:trip_id>/start/", views.start_trip, name="start"),
    path("<int:trip_id>/complete/", views.complete_trip, name="complete"),
]