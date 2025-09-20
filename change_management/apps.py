from django.apps import AppConfig


class ChangeManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'change_management'
    verbose_name = 'Change & Incident Management'

    def ready(self):
        # import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            # avoid import-time errors during migrations if dependencies missing
            pass
