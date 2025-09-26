Redis and Deploy Checklist

This project uses Django and (optionally) `django-ratelimit` for OTP resend throttling. To make rate-limiting reliable in production and across multiple processes/workers, configure a shared cache such as Redis.

Quick checklist

- Install Redis on your infrastructure (managed service or self-hosted).
  - Example: `apt install redis-server` (Debian/Ubuntu) or use AWS ElastiCache / Azure Cache for Redis.
- Create or obtain a connection URL. Example: `redis://:PASSWORD@redis-host.example.com:6379/1`.
- Set environment variables for the Django app process (systemd, Docker, etc.):
  - `REDIS_URL` — e.g. `redis://:s3cr3t@10.0.0.5:6379/1`
  - Optionally `HAWWA_CACHE_KEY_PREFIX` — e.g. `hawwa_prod`
- Ensure `django-redis` is installed (added to `requirements.txt`).
  - `pip install -r requirements.txt`
- Confirm `hawwa/settings.py` contains a `CACHES` entry that uses `django_redis.cache.RedisCache` and reads `REDIS_URL` from the environment.
- Restart application and worker processes after environment changes. If using systemd, for example:
  - `sudo systemctl daemon-reload`
  - `sudo systemctl restart hawwa.service`
  - `sudo systemctl restart hawwa-worker.service` (if present)
- For `django-ratelimit` to work across processes, set `RATELIMIT_USE_CACHE = 'default'` in `settings.py` (optional).
- Security and scaling notes:
  - Use a dedicated Redis instance or database for this application and protect it with a password and network-level controls.
  - Configure Redis persistence and memory eviction policy according to your needs.
  - Monitor and alert on Redis latency/availability; if Redis is unreachable, consider fallback behaviors for rate-limiting.

Recommended small changes post-deploy

- Consider setting `SESSION_ENGINE` to use cached DB sessions for better performance.
- Use TLS/SSL for Redis endpoints when supported by your provider.
- Rotate Redis credentials and rotate any secrets used by the app.

If you want, I can also add `RATELIMIT_USE_CACHE = 'default'` to `hawwa/settings.py` and an example `systemd` unit snippet for deployments.