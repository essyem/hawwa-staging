#!/bin/bash
# Quick start script for Hawwa Wellness

echo "🚀 Starting Hawwa Wellness Application..."
echo ""

# Generate a production secret key if not already set
SECRET_KEY_FILE="/home/azureuser/hawwa/.production_secret"
if [ ! -f "$SECRET_KEY_FILE" ]; then
    echo "Generating production secret key..."
    python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' > $SECRET_KEY_FILE
    chmod 600 $SECRET_KEY_FILE
fi

SECRET_KEY=$(cat $SECRET_KEY_FILE)

# Update the systemd service with the secret key
sudo sed -i "s/Environment=HAWWA_SECRET_KEY=.*/Environment=HAWWA_SECRET_KEY=$SECRET_KEY/" /etc/systemd/system/hawwa.service

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable hawwa.service
sudo systemctl start hawwa.service
sudo systemctl start nginx

echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if systemctl is-active --quiet hawwa.service; then
    echo "✅ Hawwa service is running"
else
    echo "❌ Hawwa service failed to start"
    echo "Checking logs..."
    sudo journalctl -u hawwa.service --no-pager -n 20
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx failed to start"
fi

echo ""
echo "🌐 Your Hawwa Wellness application should be available at:"
echo "   HTTP:  http://hawwawellness.com:8080"
echo "   Local: http://localhost:8080"
echo ""
echo "📋 Available commands:"
echo "   ./deploy.sh status    - Check service status"
echo "   ./deploy.sh logs      - View error logs"
echo "   ./deploy.sh ssl       - Setup SSL certificates"
echo "   ./deploy.sh restart   - Restart services"
echo ""
echo "🔧 Next steps:"
echo "1. Set up DNS records for hawwawellness.com → $(curl -s ifconfig.me)"
echo "2. Run './deploy.sh ssl' to setup SSL certificates"
echo "3. Update Azure Network Security Group to allow ports 8080 and 8443"