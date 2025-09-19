from django.apps import AppConfig


class HrmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrms'
    verbose_name = 'Human Resource Management System'
    
    def ready(self):
        # Import signal handlers when app is ready
        try:
            import hrms.signals
        except ImportError:
            pass
