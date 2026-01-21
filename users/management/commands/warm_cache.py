"""
Management command to warm up the cache with frequently accessed data.

This pre-populates the cache with user data to improve initial response times.
Use this after deploying new code or after cache has been cleared.

Usage:
    python manage.py warm_cache
    python manage.py warm_cache --timeout 3600
"""
from django.core.management.base import BaseCommand, CommandParser
from django.core.cache import cache
from django.conf import settings

from users.models import User
from users.serializers import UserSerializer


class Command(BaseCommand):
    help = 'Warm up the cache with frequently accessed data'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--timeout',
            type=int,
            default=getattr(settings, 'CACHE_TTL', 300),
            help='Cache timeout in seconds (default: CACHE_TTL from settings or 300)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing cache before warming'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        
        if options['clear']:
            self.stdout.write("Clearing existing cache...")
            from users.cache_utils import clear_all_cache
            cleared = clear_all_cache()
            self.stdout.write(self.style.WARNING(f"Cleared {cleared} cache entries"))
        
        self.stdout.write("Starting cache warm-up...")
        
        # Get all users
        users = User.objects.all()
        user_count = users.count()
        
        self.stdout.write(f"Found {user_count} users to cache")
        
        # Pre-cache user list
        serializer = UserSerializer(users, many=True)
        cache.set('user_list', serializer.data, timeout=timeout)
        self.stdout.write(self.style.SUCCESS("✓ Cached user list"))
        
        # Pre-cache individual users
        cached_count = 0
        for user in users:
            user_data = UserSerializer(user).data
            cache_key = f'user_{user.id}'
            cache.set(cache_key, user_data, timeout=timeout)
            cached_count += 1
            
            # Progress indicator for large datasets
            if cached_count % 100 == 0:
                self.stdout.write(f"  Cached {cached_count}/{user_count} users...")
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ Successfully cached {cached_count} individual users"
        ))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n🚀 Cache warm-up complete! "
            f"Cached {cached_count + 1} entries with {timeout}s timeout"
        ))
