from .settings import *
from pathlib import Path
import os

# Development overrides for local testing (portable across VMs)
# This file is safe to commit to the repo for development usage.
BASE_DIR = Path(__file__).resolve().parent.parent

# Allow toggling DEBUG via env var. Default to True in development images.
DEBUG = os.environ.get('HAWWA_DEBUG', 'True').lower() in ('1', 'true', 'yes')

# Allow configuration of hosts via env var; default includes common test/dev hosts
# Example: HAWWA_ALLOWED_HOSTS=localhost,127.0.0.1,my-vm
allowed = os.environ.get('HAWWA_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver')
ALLOWED_HOSTS = [h.strip() for h in allowed.split(',') if h.strip()]

# SQLite by default for simple VM developer experience. Override with HAWWA_DB_PATH
db_path = os.environ.get('HAWWA_DB_PATH')
if db_path:
    db_name = Path(db_path)
else:
    db_name = BASE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(db_name),
    }
}

# Static directory: ensure a local static directory exists on the VM
static_dir = BASE_DIR / 'static'
try:
    static_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    # Best-effort: if we can't create the dir (permissions), just ensure the setting exists
    pass
STATICFILES_DIRS = [static_dir]

# Development-friendly email backend
EMAIL_BACKEND = os.environ.get('HAWWA_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# For local development, you may want to set a non-empty secret key via env var.
# Never store production secrets here. Example: export DJANGO_SECRET_KEY='mydevkey'
if os.environ.get('DJANGO_SECRET_KEY'):
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Provide a safe default development secret key when none is provided.
# This is intentionally non-secret and only for local development/testing.
if not globals().get('SECRET_KEY'):
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-hawwa-please-change')

# Ensure the new change_management app is enabled in development
try:
    if 'change_management' not in INSTALLED_APPS:
        INSTALLED_APPS = INSTALLED_APPS + ['change_management']
except NameError:
    INSTALLED_APPS = ['change_management']


# Ensure HAWWA_SETTINGS is present in development and allow environment overrides
# This keeps dev and prod contact info consistent while allowing local overrides.
HAWWA_SETTINGS = globals().get('HAWWA_SETTINGS', {})

# Default company name if not present
HAWWA_SETTINGS.setdefault('COMPANY_NAME', 'Hawwa LLC')

# Allow overriding support email and phone via environment variables in dev
HAWWA_SETTINGS['SUPPORT_EMAIL'] = os.environ.get(
    'HAWWA_SUPPORT_EMAIL',
    HAWWA_SETTINGS.get('SUPPORT_EMAIL', 'hello@hawwawellness.com')
)
HAWWA_SETTINGS['PHONE_NUMBER'] = os.environ.get(
    'HAWWA_PHONE_NUMBER',
    HAWWA_SETTINGS.get('PHONE_NUMBER', '+974 7212 6440')
)

# Export back to globals so templates/context processors pick it up
globals()['HAWWA_SETTINGS'] = HAWWA_SETTINGS

