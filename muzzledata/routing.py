from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/cow/(?P<mode>register|verify)/$', consumers.CowDetectionConsumer.as_asgi()),
]
