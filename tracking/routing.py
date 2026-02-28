from django.urls import re_path

from .consumers import LiveTrackingConsumer

websocket_urlpatterns = [
    re_path(r"ws/tracking/(?P<vehicle_id>\d+)/$", LiveTrackingConsumer.as_asgi()),
]
