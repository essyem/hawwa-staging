from django.conf import settings


def hawwa_settings(request):
    """Expose HAWWA_SETTINGS to all templates as `HAWWA_SETTINGS`.

    Uses `django.conf.settings` to avoid importing the settings module directly
    (prevents circular imports during setup).
    """
    return {
        'HAWWA_SETTINGS': getattr(settings, 'HAWWA_SETTINGS', {}),
    }
