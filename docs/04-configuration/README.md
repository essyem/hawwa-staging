# Configuration Documentation

System configuration guides and reference documentation.

## 📋 Contents

- [**Email Configuration**](EMAIL_CONFIGURATION.md) - Email system setup and SMTP configuration
- [**Timezone Fixes**](TIMEZONE_FIXES_SUMMARY.md) - Timezone handling and fixes

## ⚙️ Configuration Files

### Django Settings
**Location:** `/root/hawwa/hawwa/settings.py`

Key configuration sections:
- Environment detection (dev vs production)
- Database settings
- Redis cache configuration
- Email backend
- Static files
- Security settings
- Module-specific settings (HRMS, Bookings, etc.)

### Environment Variables
**Production variables (systemd service):**
```bash
HAWWA_SECRET_KEY=<secret-key>
DJANGO_SETTINGS_MODULE=hawwa.settings
```

### Gunicorn Configuration
**Location:** `/root/hawwa/gunicorn_staging.conf.py`

Settings:
- Workers: 7
- Port: 8003
- Timeout: 120s
- Access logs enabled

## 📧 Email Configuration

### SMTP Settings
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password'
DEFAULT_FROM_EMAIL = 'HAWWA System <your-email@gmail.com>'
```

### Testing Email
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

## 🕐 Timezone Configuration

### Django Settings
```python
USE_TZ = True
TIME_ZONE = 'UTC'  # or your timezone
```

### Template Usage
```django
{% load tz %}
{{ datetime_object|timezone:"Africa/Nairobi" }}
```

## 🔴 Redis Configuration

### Connection Settings
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Session Storage
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## 🗄️ Database Configuration

### PostgreSQL
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hawwa',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔒 Security Configuration

### Production Security
```python
DEBUG = False
ALLOWED_HOSTS = ['staging.hawwa.online', 'hawwa.online']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### CORS (if using API)
```python
CORS_ALLOWED_ORIGINS = [
    "https://staging.hawwa.online",
    "https://hawwa.online",
]
```

## 📁 Static Files Configuration

### Settings
```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## 🔧 Module Configuration

### HRMS Settings
```python
HRMS_SIDEBAR = [
    {
        'label': 'Dashboard',
        'icon': 'fas fa-tachometer-alt',
        'url_name': 'hrms:dashboard',
    },
    # ... more items
]
```

## 🧪 Testing Configuration

### Test Settings
```python
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

## 📚 Related Documentation

- [Deployment Guide](../02-deployment/)
- [Development Setup](../01-getting-started/)
- [Architecture](../05-architecture/)
