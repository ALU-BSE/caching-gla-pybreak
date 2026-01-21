from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """
        Connect signal handlers when the app is ready.
        This ensures cache invalidation works regardless of how data is modified.
        """
        import users.cache_signals  # noqa: F401
