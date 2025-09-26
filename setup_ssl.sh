#!/bin/bash
# SSL Certificate Setup Script for Hawwa Wellness
# This version properly handles port 80 conflicts and uses standalone mode

echo "Setting up SSL certificates for Hawwa Wellness..."
echo "This script will temporarily stop nginx to obtain certificates"
echo ""

# Check if domains resolve to this server
echo "Checking DNS resolution..."
DOMAIN_IP=$(dig +short hawwawellness.com)
WWW_IP=$(dig +short www.hawwawellness.com)
SERVER_IP=$(curl -s ifconfig.me)

echo "hawwawellness.com resolves to: $DOMAIN_IP"
echo "www.hawwawellness.com resolves to: $WWW_IP"
echo "This server's public IP: $SERVER_IP"
echo ""

if [ "$DOMAIN_IP" != "$SERVER_IP" ] || [ "$WWW_IP" != "$SERVER_IP" ]; then
    echo "WARNING: DNS records don't point to this server!"
    echo "Update your DNS records first, then run this script."
    echo ""
    echo "Add these DNS records:"
    echo "A    hawwawellness.com        $SERVER_IP"
    echo "A    www.hawwawellness.com    $SERVER_IP"
    echo ""
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Exiting. Please update DNS records first."
        exit 1
    fi
fi

# Backup current nginx configuration
echo "Backing up current nginx sites..."
sudo mkdir -p /tmp/nginx_backup
sudo cp -r /etc/nginx/sites-enabled/* /tmp/nginx_backup/ 2>/dev/null || true

# Stop nginx temporarily to free up port 80
echo "Temporarily stopping nginx to obtain SSL certificate..."
sudo systemctl stop nginx

# Obtain SSL certificate using standalone mode
echo "Obtaining SSL certificate using standalone mode..."
sudo certbot certonly --standalone \
    -d hawwawellness.com \
    -d www.hawwawellness.com \
    --non-interactive \
    --agree-tos \
    --email hello@hawwawellness.com \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    echo "SSL certificate obtained successfully!"
    
    # Enable SSL in hawwa nginx config
    echo "Enabling SSL configuration for Hawwa..."
    
    # Create the SSL-enabled configuration
    cat > /tmp/hawwa_ssl_config << 'EOF'
server {
    listen 8080;
    server_name hawwawellness.com www.hawwawellness.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name:8443$request_uri;
}

server {
    listen 8443 ssl http2;
    server_name hawwawellness.com www.hawwawellness.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/hawwawellness.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hawwawellness.com/privkey.pem;
    
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
    sudo cp /tmp/hawwa_ssl_config /etc/nginx/sites-available/hawwa
    
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
        echo "Certificate renewal test passed!"
        echo ""
        echo "🎉 SSL setup complete! 🎉"
        echo ""
        echo "Your Hawwa Wellness site is now available at:"
        echo "HTTP:  http://hawwawellness.com:8080 (redirects to HTTPS)"
        echo "HTTPS: https://hawwawellness.com:8443"
        echo ""
        echo "Certificate will auto-renew. Check with: sudo certbot certificates"
    else
        echo "Certificate renewal test failed. Check configuration."
    fi
else
    echo "Failed to obtain SSL certificate."
    echo "Starting nginx again..."
    sudo systemctl start nginx
    echo ""
    echo "Make sure:"
    echo "1. DNS records point to this server ($SERVER_IP)"
    echo "2. Firewall allows HTTP traffic on port 80"
    echo "3. Domain is accessible from the internet"
    echo ""
    echo "You can check if the domain resolves correctly:"
    echo "  nslookup hawwawellness.com"
    echo "  curl -I http://hawwawellness.com"
fi

echo ""
echo "Cleaning up temporary files..."
rm -f /tmp/hawwa_ssl_config
sudo rm -rf /tmp/nginx_backup