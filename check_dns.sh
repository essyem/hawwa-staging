#!/bin/bash
# DNS and SSL Diagnosis Script for Hawwa Wellness

echo "🔍 Hawwa Wellness DNS & SSL Diagnosis"
echo "======================================"
echo ""

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)
echo "🖥️  This server's public IP: $SERVER_IP"
echo ""

# Check DNS resolution
echo "🌐 DNS Resolution Check:"
echo "------------------------"

DOMAIN_IP=$(dig +short hawwawellness.com)
WWW_IP=$(dig +short www.hawwawellness.com)

echo "hawwawellness.com      → $DOMAIN_IP"
echo "www.hawwawellness.com  → $WWW_IP"
echo ""

# Check which domains resolve correctly
DOMAIN_OK=false
WWW_OK=false

if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
    echo "✅ hawwawellness.com points to this server"
    DOMAIN_OK=true
else
    echo "❌ hawwawellness.com points to $DOMAIN_IP (should be $SERVER_IP)"
fi

if [ "$WWW_IP" = "$SERVER_IP" ]; then
    echo "✅ www.hawwawellness.com points to this server"
    WWW_OK=true
else
    echo "❌ www.hawwawellness.com points to $WWW_IP (should be $SERVER_IP)"
fi

echo ""

# Check what's currently served
echo "🌍 Current Web Response Check:"
echo "------------------------------"

echo "Testing hawwawellness.com:"
RESPONSE=$(curl -s -I http://hawwawellness.com | head -1)
echo "  Response: $RESPONSE"

echo ""

# Provide options
echo "🛠️  Available Options:"
echo "====================="
echo ""

if [ "$DOMAIN_OK" = true ] && [ "$WWW_OK" = true ]; then
    echo "🎉 Both domains point to this server! You can proceed with SSL setup."
    echo ""
    echo "Run: ./setup_ssl.sh"
    
elif [ "$WWW_OK" = true ] && [ "$DOMAIN_OK" = false ]; then
    echo "📝 Option 1: Update DNS (Recommended)"
    echo "   Update your DNS provider to point hawwawellness.com to $SERVER_IP"
    echo "   Then run: ./setup_ssl.sh"
    echo ""
    
    echo "🔧 Option 2: SSL for www subdomain only"
    echo "   Get SSL certificate for www.hawwawellness.com only"
    echo "   Run: ./setup_ssl_www_only.sh"
    echo ""
    
    echo "⚡ Option 3: Force SSL setup (may fail)"
    echo "   Try SSL setup anyway with current DNS"
    echo "   Run: ./setup_ssl.sh and answer 'y' to continue"
    
elif [ "$DOMAIN_OK" = true ] && [ "$WWW_OK" = false ]; then
    echo "📝 Option 1: Update DNS (Recommended)"
    echo "   Update your DNS provider to point www.hawwawellness.com to $SERVER_IP"
    echo "   Then run: ./setup_ssl.sh"
    echo ""
    
    echo "🔧 Option 2: SSL for main domain only"
    echo "   Get SSL certificate for hawwawellness.com only"
    echo "   Run: ./setup_ssl_main_only.sh"
    
else
    echo "❗ Both domains need DNS updates"
    echo "   Update your DNS provider:"
    echo "   A    hawwawellness.com        $SERVER_IP"
    echo "   A    www.hawwawellness.com    $SERVER_IP"
    echo ""
    echo "   Then run: ./setup_ssl.sh"
fi

echo ""
echo "🔍 DNS Propagation Check:"
echo "------------------------"
echo "You can check DNS propagation at: https://dnschecker.org"
echo "Search for: hawwawellness.com and www.hawwawellness.com"
echo ""

echo "💡 Current working access:"
echo "-------------------------"
echo "HTTP:  http://$SERVER_IP:8080"
echo "HTTPS: https://$SERVER_IP:8443 (after SSL setup)"
echo ""

if [ "$WWW_OK" = true ]; then
    echo "Also working:"
    echo "HTTP:  http://www.hawwawellness.com:8080"
fi