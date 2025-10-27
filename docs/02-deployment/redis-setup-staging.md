# Redis Setup for Hawwa Staging

## Issue Resolution: Redis Connection Error

### Problem
The HRMS reports page (`/hrms/reports/`) was throwing Redis connection errors:
```
redis.exceptions.ConnectionError: Error 111 connecting to 127.0.0.1:6379. Connection refused.
```

### Root Cause
- Redis server was not installed on the staging environment
- Django application was configured to use Redis for caching but Redis service was missing
- This caused HRMS API endpoints (like `/hrms/api/v1/reports/status/`) to fail

### Solution Applied

#### 1. Installed Redis Server
```bash
apt update && apt install -y redis-server redis-tools
```

#### 2. Started and Enabled Redis Service
```bash
systemctl start redis-server
systemctl enable redis-server
```

#### 3. Verified Redis Configuration
- **Redis URL**: `redis://127.0.0.1:6379/1` (configured in Django settings)
- **Django Backend**: `django_redis.cache.RedisCache`
- **Connection**: Tested and working

#### 4. Restarted Application
```bash
systemctl restart hawwa-stg
```

### Verification Steps

#### Redis Service Status
```bash
systemctl status redis-server
# Should show: Active: active (running)
```

#### Redis Connectivity Test
```bash
redis-cli ping
# Should return: PONG
```

#### Django Cache Test
```python
from django.core.cache import cache
cache.set('test_key', 'test_value', 30)
result = cache.get('test_key')
# Should return: test_value
```

### Result
✅ **FIXED**: HRMS reports and API endpoints now work properly
✅ **Performance**: Redis caching improves application performance
✅ **Stability**: No more Redis connection errors in logs

### Configuration Details

#### Django Settings (`hawwa/settings.py`)
```python
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### Redis Service Configuration
- **Port**: 6379 (default)
- **Database**: 1 (as configured in REDIS_URL)
- **Memory**: ~3.3MB usage
- **Auto-start**: Enabled on boot

### Maintenance

#### Monitoring Redis
```bash
# Check Redis status
systemctl status redis-server

# Monitor Redis memory usage
redis-cli info memory

# Check Redis logs
journalctl -u redis-server -f
```

#### Performance Tuning (if needed)
- Redis configuration: `/etc/redis/redis.conf`
- Memory limit: Can be set with `maxmemory` directive
- Persistence: RDB snapshots enabled by default

### Notes
- Redis is now required for proper HRMS functionality
- All HRMS reports, analytics, and API endpoints depend on Redis caching
- Redis provides session storage and query result caching for better performance

---
**Date**: October 19, 2025
**Environment**: staging.hawwa.online
**Status**: ✅ Resolved