from typing import Optional

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer
from users.cache_utils import cache_performance, get_cache_stats, clear_all_cache


def get_cache_key(prefix: str, identifier: Optional[str] = None) -> str:
    """Generate consistent cache keys."""
    if identifier is not None:
        return f"{prefix}_{identifier}"
    return prefix


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @cache_performance("user_list_cache")
    def list(self, request, *args, **kwargs):
        cache_key = get_cache_key('user_list')
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=settings.CACHE_TTL)
        return response

    @cache_performance("user_detail_cache")
    def retrieve(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        cache_key = get_cache_key('user', user_id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=settings.CACHE_TTL)
        return response

    def perform_create(self, serializer):
        response = super().perform_create(serializer)
        cache.delete(get_cache_key('user_list'))
        return response

    def perform_update(self, serializer):
        response = super().perform_update(serializer)
        user_id = serializer.instance.id
        cache.delete(get_cache_key('user_list'))
        cache.delete(get_cache_key('user', user_id))
        return response

    def perform_destroy(self, instance):
        user_id = instance.id
        cache.delete(get_cache_key('user_list'))
        cache.delete(get_cache_key('user', user_id))
        return super().perform_destroy(instance)


@api_view(['GET'])
def cache_stats_view(request):
    """
    API endpoint to get cache statistics.
    
    Returns information about:
    - Total cached keys
    - Cache hit/miss rates
    - Redis memory usage
    - Connection statistics
    """
    stats = get_cache_stats()
    return Response(stats)


@api_view(['POST'])
def clear_cache_view(request):
    """
    API endpoint to clear all cache entries.
    
    Use with caution - this will clear the entire cache.
    """
    cleared_count = clear_all_cache()
    return Response({
        'status': 'success',
        'message': f'Cleared {cleared_count} cache entries'
    }, status=status.HTTP_200_OK)
