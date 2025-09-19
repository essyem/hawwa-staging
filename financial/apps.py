from django.apps import AppConfig


class FinancialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial'

    def ready(self):
        # Import signals to wire up posting on payment/expense events
        from . import signals  # noqa: F401
