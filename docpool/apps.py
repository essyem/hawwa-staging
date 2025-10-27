from django.apps import AppConfig


class DocpoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'docpool'
    verbose_name = 'Document Pool'
    
    def ready(self):
        """Initialize app when Django starts"""
        pass
