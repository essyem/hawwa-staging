# Deployment Documentation

This section contains all deployment-related documentation for staging and production environments.

## 📋 Contents

- [**Deployment Guide**](DEPLOY.md) - Complete deployment instructions
- [**Redis Setup**](redis-setup-staging.md) - Redis installation and configuration

## 🌍 Environments

### Staging Environment
- **URL:** https://staging.hawwa.online
- **Port:** 8003 (internal)
- **Service:** `hawwa-stg.service`
- **Gunicorn Config:** `/root/hawwa/gunicorn_staging.conf.py`
- **SSL:** Let's Encrypt (auto-renewing)

### Production Environment
- **URL:** TBD
- **Port:** TBD
- **Service:** TBD
- **Status:** Planned

## 🚀 Quick Deployment

### Staging Deployment
```bash
# 1. Pull latest code
cd /root/hawwa
git pull origin master

# 2. Activate environment
source env-hawwa/bin/activate

# 3. Install/update dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Restart service
sudo systemctl restart hawwa-stg
```

### Check Service Status
```bash
sudo systemctl status hawwa-stg
sudo journalctl -u hawwa-stg -f
```

## 🔧 Infrastructure Components

### Web Server: Nginx
- Config: `/etc/nginx/sites-available/staging.hawwa.online`
- SSL Certs: `/etc/letsencrypt/live/staging.hawwa.online/`
- Logs: `/var/log/nginx/`

### Application Server: Gunicorn
- Workers: 7 (2 * CPU + 1)
- Timeout: 120 seconds
- Bind: 127.0.0.1:8003

### Cache Server: Redis
- Version: 7.0.15
- Port: 6379
- Database: 1 (for Django cache)
- Config: `/etc/redis/redis.conf`

### Database: PostgreSQL
- Version: 14+
- Database: `hawwa`
- Connection: Django ORM

## 📊 Monitoring

### Service Health
```bash
# Check all services
sudo systemctl status hawwa-stg nginx redis-server postgresql

# View application logs
sudo journalctl -u hawwa-stg -n 100

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Check Redis
redis-cli ping
redis-cli info stats
```

### Resource Monitoring
```bash
# CPU and Memory
htop
free -h

# Disk usage
df -h

# Network
netstat -tlnp
```

## 🔒 Security

### SSL Certificates
```bash
# Check expiry
sudo certbot certificates

# Manual renewal
sudo certbot renew

# Auto-renewal (configured)
sudo systemctl status certbot.timer
```

### Firewall
```bash
# Check firewall status
sudo ufw status

# Common ports
# 22 - SSH
# 80 - HTTP (redirects to HTTPS)
# 443 - HTTPS
# 6379 - Redis (localhost only)
# 5432 - PostgreSQL (localhost only)
```

## 🔄 Rollback Procedure

If deployment fails:
```bash
# 1. Check git log
git log --oneline -10

# 2. Rollback to previous commit
git reset --hard <previous-commit-hash>

# 3. Restart service
sudo systemctl restart hawwa-stg

# 4. Verify
curl -I https://staging.hawwa.online
```

## 📚 Related Documentation

- [Configuration Guide](../04-configuration/)
- [Project Management](../07-project-management/)
- [Architecture](../05-architecture/)
