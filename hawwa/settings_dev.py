from .settings import *
from pathlib import Path

# Development overrides for local testing (uses SQLite)
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Use a lightweight SQLite DB for local dev in Codespace
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Ensure STATIC directory exists so system checks don't warn
STATICFILES_DIRS = [BASE_DIR / 'static']

# Use a simpler email backend in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
