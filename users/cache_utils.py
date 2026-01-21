"""
Cache utility functions and decorators for performance monitoring.

This module provides:
- Performance monitoring decorator for cache operations
- Cache tagging utilities for better invalidation
- Helper functions for cache management
"""
import functools
import time
import logging
from typing import List, Set, Optional, Any, Callable

from django.core.cache import cache

logger = logging.getLogger(__name__)


def cache_performance(cache_name: str) -> Callable:
    """
    Decorator to track cache performance (hit/miss and timing).
    
    Usage:
        @cache_performance("user_list_cache")
        def list(self, request, *args, **kwargs):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed = end_time - start_time
            
            logger.info(f"[CACHE PERF] {cache_name}: {elapsed:.4f}s")
            return result
        return wrapper
    return decorator


def cache_with_tags(key: str, data: Any, tags: List[str], timeout: int = 300) -> None:
    """
    Cache data with associated tags for easier invalidation.
    
    Args:
        key: The cache key
        data: The data to cache
        tags: List of tags to associate with this cache entry
        timeout: Cache timeout in seconds
    """
    cache.set(key, data, timeout)
    
    for tag in tags:
        tag_key = f'tag_{tag}'
        tagged_keys: Set[str] = cache.get(tag_key, set())
        tagged_keys.add(key)
        cache.set(tag_key, tagged_keys, timeout)
    
    logger.debug(f"Cached {key} with tags: {tags}")


def invalidate_by_tag(tag: str) -> int:
    """
    Invalidate all cache entries associated with a tag.
    
    Args:
        tag: The tag whose associated cache entries should be invalidated
        
    Returns:
        Number of cache entries invalidated
    """
    tag_key = f'tag_{tag}'
    tagged_keys: Set[str] = cache.get(tag_key, set())
    
    count = 0
    for key in tagged_keys:
        cache.delete(key)
        count += 1
        logger.debug(f"Invalidated cache key: {key}")
    
    cache.delete(tag_key)
    logger.info(f"Invalidated {count} cache entries for tag: {tag}")
    
    return count


def get_cache_stats() -> dict:
    """
    Get cache statistics using Redis INFO command.
    
    Returns:
        Dictionary containing cache statistics
    """
    try:
        # Access the underlying Redis client
        from django_redis import get_redis_connection
        redis_client = get_redis_connection("default")
        
        # Get Redis INFO
        info = redis_client.info()
        
        # Get all keys matching our pattern
        keys = redis_client.keys('*')
        
        stats = {
            'total_keys': len(keys),
            'keys': [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys[:100]],  # Limit to first 100
            'redis_version': info.get('redis_version', 'unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', 'unknown'),
            'used_memory_peak_human': info.get('used_memory_peak_human', 'unknown'),
            'total_connections_received': info.get('total_connections_received', 0),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': calculate_hit_rate(info.get('keyspace_hits', 0), info.get('keyspace_misses', 0)),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0),
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            'error': str(e),
            'total_keys': 0,
            'keys': [],
        }


def calculate_hit_rate(hits: int, misses: int) -> str:
    """Calculate cache hit rate percentage."""
    total = hits + misses
    if total == 0:
        return "N/A (no requests yet)"
    rate = (hits / total) * 100
    return f"{rate:.2f}%"


def clear_all_cache() -> int:
    """
    Clear all cache entries.
    
    Returns:
        Number of keys deleted
    """
    try:
        from django_redis import get_redis_connection
        redis_client = get_redis_connection("default")
        
        keys = redis_client.keys('*')
        count = len(keys)
        
        if keys:
            redis_client.delete(*keys)
        
        logger.info(f"Cleared {count} cache entries")
        return count
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return 0
