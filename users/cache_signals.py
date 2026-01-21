"""
Cache invalidation signals for User model.

This module implements signal-based cache invalidation to ensure
cache consistency when data changes occur through any method
(API, admin panel, shell, etc.)
"""
import logging
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import User

logger = logging.getLogger(__name__)


def get_cache_key(prefix: str, identifier=None) -> str:
    """Generate consistent cache keys."""
    if identifier is not None:
        return f"{prefix}_{identifier}"
    return prefix


@receiver(post_save, sender=User)
def invalidate_user_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate user-related caches when a user is created or updated.
    
    This ensures cache consistency regardless of how the user was modified
    (via API, admin panel, shell, etc.)
    """
    cache_keys_to_delete = [
        get_cache_key('user_list'),  # Always invalidate the list cache
        get_cache_key('user', instance.id),  # Invalidate individual user cache
    ]
    
    for cache_key in cache_keys_to_delete:
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")
    
    action = "created" if created else "updated"
    logger.info(f"User {instance.id} was {action}, cache invalidated.")


@receiver(post_delete, sender=User)
def invalidate_user_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate user-related caches when a user is deleted.
    """
    cache_keys_to_delete = [
        get_cache_key('user_list'),
        get_cache_key('user', instance.id),
    ]
    
    for cache_key in cache_keys_to_delete:
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")
    
    logger.info(f"User {instance.id} was deleted, cache invalidated.")
