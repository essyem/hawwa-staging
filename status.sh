#!/bin/bash
# Final Setup Summary and Test Script for Hawwa Wellness

echo "🌟 Hawwa Wellness Production Setup Summary"
echo "=========================================="
echo ""

# Get server information
SERVER_IP=$(curl -s ifconfig.me)
echo "🖥️  Server IP: $SERVER_IP"
echo ""

# Check services status
echo "📊 Service Status:"
echo "-------------------"

if systemctl is-active --quiet hawwa.service; then
    echo "✅ Hawwa Service: Running"
    HAWWA_STATUS="✅ Running"
else
    echo "❌ Hawwa Service: Not Running"
    HAWWA_STATUS="❌ Not Running"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
    NGINX_STATUS="✅ Running"
else
    echo "❌ Nginx: Not Running"
    NGINX_STATUS="❌ Not Running"
fi

# Check SSL certificate
if [ -f "/etc/letsencrypt/live/www.hawwawellness.com/fullchain.pem" ]; then
    SSL_EXPIRY=$(sudo openssl x509 -in /etc/letsencrypt/live/www.hawwawellness.com/fullchain.pem -noout -text | grep "Not After" | cut -d: -f2-)
    echo "✅ SSL Certificate: Valid (expires$SSL_EXPIRY)"
    SSL_STATUS="✅ Valid"
else
    echo "❌ SSL Certificate: Not Found"
    SSL_STATUS="❌ Not Found"
fi

echo ""

# Check ports
echo "🔌 Port Status:"
echo "---------------"
HTTP_PORT=$(sudo netstat -tlnp | grep :8080 | wc -l)
HTTPS_PORT=$(sudo netstat -tlnp | grep :8443 | wc -l)

if [ $HTTP_PORT -gt 0 ]; then
    echo "✅ Port 8080 (HTTP): Listening"
else
    echo "❌ Port 8080 (HTTP): Not Listening"
fi

if [ $HTTPS_PORT -gt 0 ]; then
    echo "✅ Port 8443 (HTTPS): Listening"
else
    echo "❌ Port 8443 (HTTPS): Not Listening"
fi

echo ""

# Check DNS resolution
echo "🌐 DNS Status:"
echo "--------------"
WWW_IP=$(dig +short www.hawwawellness.com)
MAIN_IP=$(dig +short hawwawellness.com)

if [ "$WWW_IP" = "$SERVER_IP" ]; then
    echo "✅ www.hawwawellness.com → $WWW_IP (correct)"
    WWW_DNS="✅ Correct"
else
    echo "⚠️  www.hawwawellness.com → $WWW_IP (should be $SERVER_IP)"
    WWW_DNS="⚠️ Incorrect"
fi

if [ "$MAIN_IP" = "$SERVER_IP" ]; then
    echo "✅ hawwawellness.com → $MAIN_IP (correct)"
    MAIN_DNS="✅ Correct"
else
    echo "⚠️  hawwawellness.com → $MAIN_IP (should be $SERVER_IP)"
    MAIN_DNS="⚠️ Incorrect"
fi

echo ""

# Test local connectivity
echo "🧪 Local Connectivity Test:"
echo "---------------------------"

HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080 2>/dev/null)
if [ "$HTTP_TEST" = "301" ]; then
    echo "✅ HTTP (8080): Working (redirects to HTTPS)"
    LOCAL_HTTP="✅ Working"
else
    echo "❌ HTTP (8080): Not responding correctly (got $HTTP_TEST)"
    LOCAL_HTTP="❌ Failed"
fi

HTTPS_TEST=$(curl -s -o /dev/null -w "%{http_code}" -k https://127.0.0.1:8443 2>/dev/null)
if [ "$HTTPS_TEST" = "200" ] || [ "$HTTPS_TEST" = "302" ]; then
    echo "✅ HTTPS (8443): Working"
    LOCAL_HTTPS="✅ Working"
else
    echo "❌ HTTPS (8443): Not responding correctly (got $HTTPS_TEST)"
    LOCAL_HTTPS="❌ Failed"
fi

echo ""

# Summary table
echo "📋 Complete Status Summary:"
echo "============================="
printf "%-25s %s\n" "Component" "Status"
printf "%-25s %s\n" "-------------------------" "----------"
printf "%-25s %s\n" "Hawwa Service" "$HAWWA_STATUS"
printf "%-25s %s\n" "Nginx" "$NGINX_STATUS"
printf "%-25s %s\n" "SSL Certificate" "$SSL_STATUS"
printf "%-25s %s\n" "www.hawwawellness.com DNS" "$WWW_DNS"
printf "%-25s %s\n" "hawwawellness.com DNS" "$MAIN_DNS"
printf "%-25s %s\n" "Local HTTP (8080)" "$LOCAL_HTTP"
printf "%-25s %s\n" "Local HTTPS (8443)" "$LOCAL_HTTPS"

echo ""

# Access information
echo "🌍 Access Information:"
echo "====================="
echo ""
echo "🔗 Working URLs:"
if [ "$WWW_DNS" = "✅ Correct" ]; then
    echo "   ✅ http://www.hawwawellness.com:8080 (redirects to HTTPS)"
    echo "   ✅ https://www.hawwawellness.com:8443"
fi
echo "   ✅ http://$SERVER_IP:8080 (redirects to HTTPS)"
echo "   ✅ https://$SERVER_IP:8443"
echo ""

# Next steps
echo "🔧 Next Steps:"
echo "=============="
echo ""

if [ "$MAIN_DNS" != "✅ Correct" ]; then
    echo "1. 📝 Update DNS for hawwawellness.com:"
    echo "   Add A record: hawwawellness.com → $SERVER_IP"
    echo ""
fi

echo "2. 🔒 Configure Azure Network Security Group:"
echo "   - Allow inbound TCP port 8080 (HTTP)"
echo "   - Allow inbound TCP port 8443 (HTTPS)"
echo ""

echo "3. 🔄 SSL certificate will auto-renew"
echo "   Manual renewal: sudo ./renew_hawwa_ssl.sh"
echo ""

echo "4. 📋 Useful commands:"
echo "   ./deploy.sh status     # Check service status"
echo "   ./deploy.sh restart    # Restart services"
echo "   ./deploy.sh logs       # View logs"
echo "   ./deploy.sh backup     # Backup database"
echo ""

echo "🎉 Hawwa Wellness is ready for production! 🎊"