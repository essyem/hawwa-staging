from django.conf import settings

def hawwa_settings(request):
    """Expose HAWWA_SETTINGS to templates as `HAWWA_SETTINGS`."""
    return {
        'HAWWA_SETTINGS': getattr(settings, 'HAWWA_SETTINGS', {}),
    }
def hawwa_settings(request):
    """Expose HAWWA_SETTINGS to all templates."""
    from .settings import HAWWA_SETTINGS
    return {
        'HAWWA_SETTINGS': HAWWA_SETTINGS
    }
