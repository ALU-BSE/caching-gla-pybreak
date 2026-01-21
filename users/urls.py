from django.urls import path, include
from rest_framework import routers

from users.views import UserViewSet, cache_stats_view, clear_cache_view

router = routers.DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('cache/stats/', cache_stats_view, name='cache-stats'),
    path('cache/clear/', clear_cache_view, name='cache-clear'),
] + router.urls