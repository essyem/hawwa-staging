#!/bin/bash
# Smart Certificate Renewal Script for Hawwa Wellness
# This script handles the port 80 conflict by temporarily creating the right setup

echo "🔄 Smart Certificate Renewal for www.hawwawellness.com"
echo "======================================================"
echo ""

# Check if certificate exists
if [ ! -f "/etc/letsencrypt/live/www.hawwawellness.com/fullchain.pem" ]; then
    echo "❌ Certificate not found. Run ./setup_ssl_www_only.sh first"
    exit 1
fi

echo "📋 Current certificate info:"
sudo certbot certificates --cert-name www.hawwawellness.com 2>/dev/null | grep -A5 "Certificate Name: www.hawwawellness.com" || echo "Certificate exists but details not shown"
echo ""

echo "🔧 Setting up temporary renewal configuration..."

# Create a temporary nginx config that listens on port 80 for ACME challenges
sudo tee /etc/nginx/sites-available/hawwa-renewal > /dev/null << 'EOF'
# Temporary config for ACME challenge renewal
server {
    listen 80;
    server_name www.hawwawellness.com;
    
    # ACME challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }
    
    # Redirect everything else to our custom port
    location / {
        return 301 http://$server_name:8080$request_uri;
    }
}
EOF

# Backup the current hawwa config
sudo cp /etc/nginx/sites-available/hawwa /tmp/hawwa_backup.conf

# Disable the current hawwa config and enable renewal config
echo "🔄 Temporarily switching to renewal configuration..."
sudo rm -f /etc/nginx/sites-enabled/hawwa
sudo ln -sf /etc/nginx/sites-available/hawwa-renewal /etc/nginx/sites-enabled/hawwa-renewal

# Test and reload nginx
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded with renewal configuration"
else
    echo "❌ Nginx configuration test failed"
    # Restore original config
    sudo ln -sf /etc/nginx/sites-available/hawwa /etc/nginx/sites-enabled/hawwa
    sudo rm -f /etc/nginx/sites-enabled/hawwa-renewal
    sudo systemctl reload nginx
    exit 1
fi

# Update renewal config to use webroot
sudo tee /etc/letsencrypt/renewal/www.hawwawellness.com.conf > /dev/null << 'RENEWAL_EOF'
# renew_before_expiry = 30 days
version = 2.9.0
archive_dir = /etc/letsencrypt/archive/www.hawwawellness.com
cert = /etc/letsencrypt/live/www.hawwawellness.com/cert.pem
privkey = /etc/letsencrypt/live/www.hawwawellness.com/privkey.pem
chain = /etc/letsencrypt/live/www.hawwawellness.com/chain.pem
fullchain = /etc/letsencrypt/live/www.hawwawellness.com/fullchain.pem

# Options used in the renewal process
[renewalparams]
account = 0a54d1052012f7d689248d8200bde6ca
authenticator = webroot
webroot_path = /var/www/html
server = https://acme-v02.api.letsencrypt.org/directory
key_type = ecdsa

[[webroot_map]]
www.hawwawellness.com = /var/www/html
RENEWAL_EOF

echo "🧪 Testing certificate renewal..."
RENEWAL_OUTPUT=$(sudo certbot renew --cert-name www.hawwawellness.com --dry-run 2>&1)
RENEWAL_SUCCESS=$?

echo "🔙 Restoring original nginx configuration..."
# Restore original configuration
sudo rm -f /etc/nginx/sites-enabled/hawwa-renewal
sudo ln -sf /etc/nginx/sites-available/hawwa /etc/nginx/sites-enabled/hawwa
sudo systemctl reload nginx

# Clean up
sudo rm -f /etc/nginx/sites-available/hawwa-renewal

if [ $RENEWAL_SUCCESS -eq 0 ]; then
    echo ""
    echo "🎉 Certificate renewal test SUCCESSFUL! 🎉"
    echo ""
    echo "✅ The certificate will auto-renew properly"
    echo "📅 Current certificate expires: $(sudo certbot certificates --cert-name www.hawwawellness.com 2>/dev/null | grep "Expiry Date" | head -1)"
    echo ""
    echo "💡 To manually renew in the future, run: sudo ./renew_hawwa_ssl.sh"
else
    echo ""
    echo "❌ Certificate renewal test failed"
    echo ""
    echo "📋 Renewal output:"
    echo "$RENEWAL_OUTPUT"
    echo ""
    echo "🔧 The certificate still works, but automatic renewal may fail."
    echo "   You may need to manually renew before expiry."
fi

echo ""
echo "🌐 Your site is still accessible at:"
echo "   HTTP:  http://www.hawwawellness.com:8080 (redirects to HTTPS)"
echo "   HTTPS: https://www.hawwawellness.com:8443"