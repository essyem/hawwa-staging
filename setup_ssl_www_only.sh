#!/bin/bash
# SSL Certificate Setup for www.hawwawellness.com only
# This script sets up SSL for the www subdomain only since the main domain points elsewhere

echo "Setting up SSL certificate for www.hawwawellness.com..."
echo "This will work since www.hawwawellness.com points to this server"
echo ""

SERVER_IP=$(curl -s ifconfig.me)
WWW_IP=$(dig +short www.hawwawellness.com)

echo "www.hawwawellness.com resolves to: $WWW_IP"
echo "This server's public IP: $SERVER_IP"
echo ""

if [ "$WWW_IP" != "$SERVER_IP" ]; then
    echo "❌ www.hawwawellness.com doesn't point to this server!"
    echo "Cannot obtain SSL certificate."
    exit 1
fi

echo "✅ www.hawwawellness.com points to this server. Proceeding..."
echo ""

# Backup current nginx configuration
echo "Backing up current nginx sites..."
sudo mkdir -p /tmp/nginx_backup
sudo cp -r /etc/nginx/sites-enabled/* /tmp/nginx_backup/ 2>/dev/null || true

# Stop nginx temporarily to free up port 80
echo "Temporarily stopping nginx to obtain SSL certificate..."
sudo systemctl stop nginx

# Obtain SSL certificate using standalone mode for www subdomain only
echo "Obtaining SSL certificate for www.hawwawellness.com..."
sudo certbot certonly --standalone \
    -d www.hawwawellness.com \
    --non-interactive \
    --agree-tos \
    --email hello@hawwawellness.com \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    echo "SSL certificate obtained successfully!"
    
    # Create SSL-enabled configuration for www subdomain
    echo "Creating SSL configuration for www.hawwawellness.com..."
    
    cat > /tmp/hawwa_www_ssl_config << 'EOF'
# HTTP Configuration - redirects to HTTPS
server {
    listen 8080;
    server_name www.hawwawellness.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name:8443$request_uri;
}

# HTTPS Configuration
server {
    listen 8443 ssl http2;
    server_name www.hawwawellness.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/www.hawwawellness.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.hawwawellness.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:HAWWA_SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Client max body size for file uploads
    client_max_body_size 100M;
    
    # Logging
    access_log /var/log/nginx/hawwa_ssl_access.log;
    error_log /var/log/nginx/hawwa_ssl_error.log;
    
    # Static files
    location /static/ {
        alias /home/azureuser/hawwa/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
    
    # Media files
    location /media/ {
        alias /home/azureuser/hawwa/media/;
        expires 1y;
        add_header Cache-Control "public";
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
    
    # Favicon
    location = /favicon.ico {
        alias /home/azureuser/hawwa/staticfiles/favicon.ico;
        log_not_found off;
        access_log off;
    }
    
    # Robots.txt
    location = /robots.txt {
        alias /home/azureuser/hawwa/staticfiles/robots.txt;
        log_not_found off;
        access_log off;
    }
    
    # Main application
    location / {
        proxy_pass http://unix:/home/azureuser/hawwa/hawwa.sock;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health/ {
        proxy_pass http://unix:/home/azureuser/hawwa/hawwa.sock;
        access_log off;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF
    
    # Update the hawwa nginx configuration
    sudo cp /tmp/hawwa_www_ssl_config /etc/nginx/sites-available/hawwa
    
    # Start nginx
    echo "Starting nginx with SSL configuration..."
    sudo systemctl start nginx
    
    # Test nginx configuration
    if sudo nginx -t; then
        sudo systemctl reload nginx
        echo "Nginx reloaded successfully with SSL configuration!"
    else
        echo "Nginx configuration test failed. Restoring backup..."
        sudo cp /tmp/nginx_backup/* /etc/nginx/sites-enabled/ 2>/dev/null || true
        sudo systemctl start nginx
        exit 1
    fi
    
    echo "Setting up automatic renewal..."
    
    # Create renewal hook to reload nginx
    sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
    sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null << 'HOOK_EOF'
#!/bin/bash
systemctl reload nginx
HOOK_EOF
    sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
    
    # Test renewal
    sudo certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 SSL setup complete for www.hawwawellness.com! 🎉"
        echo ""
        echo "Your Hawwa Wellness site is now available at:"
        echo "HTTP:  http://www.hawwawellness.com:8080 (redirects to HTTPS)"
        echo "HTTPS: https://www.hawwawellness.com:8443"
        echo ""
        echo "📝 Note: hawwawellness.com (without www) still points to another server."
        echo "   To get SSL for both domains, update DNS for hawwawellness.com to point to $SERVER_IP"
        echo ""
        echo "Certificate will auto-renew. Check with: sudo certbot certificates"
    else
        echo "Certificate renewal test failed. Check configuration."
    fi
else
    echo "Failed to obtain SSL certificate for www.hawwawellness.com"
    echo "Starting nginx again..."
    sudo systemctl start nginx
fi

echo ""
echo "Cleaning up temporary files..."
rm -f /tmp/hawwa_www_ssl_config
sudo rm -rf /tmp/nginx_backup