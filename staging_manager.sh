#!/bin/bash
#
# Hawwa Staging Environment Management Script
# staging.hawwa.online - Port 8003
#

HAWWA_DIR="/root/hawwa"
SERVICE_NAME="hawwa-stg"
LOG_DIR="$HAWWA_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_status() {
    echo -e "${BLUE}=== Hawwa Staging Environment Status ===${NC}"
    echo
    
    # Service status
    echo -e "${YELLOW}Service Status:${NC}"
    systemctl status $SERVICE_NAME --no-pager -l
    echo
    
    # Port check
    echo -e "${YELLOW}Port 8003 Status:${NC}"
    netstat -tlnp | grep :8003 || echo "Port 8003 not in use"
    echo
    
    # Nginx status
    echo -e "${YELLOW}Nginx Configuration:${NC}"
    nginx -t
    echo
    
    # SSL Certificate
    echo -e "${YELLOW}SSL Certificate:${NC}"
    certbot certificates -d staging.hawwa.online 2>/dev/null || echo "No certificate found"
    echo
    
    # Recent logs
    echo -e "${YELLOW}Recent Logs (last 10 lines):${NC}"
    if [ -f "$LOG_DIR/gunicorn_staging_error.log" ]; then
        tail -10 "$LOG_DIR/gunicorn_staging_error.log"
    else
        echo "No error logs found"
    fi
}

start_staging() {
    echo -e "${GREEN}Starting Hawwa Staging Environment...${NC}"
    systemctl start $SERVICE_NAME
    sleep 2
    show_status
}

stop_staging() {
    echo -e "${RED}Stopping Hawwa Staging Environment...${NC}"
    systemctl stop $SERVICE_NAME
    sleep 2
    systemctl status $SERVICE_NAME --no-pager
}

restart_staging() {
    echo -e "${YELLOW}Restarting Hawwa Staging Environment...${NC}"
    systemctl restart $SERVICE_NAME
    sleep 3
    show_status
}

reload_staging() {
    echo -e "${YELLOW}Reloading Hawwa Staging (graceful restart)...${NC}"
    systemctl reload $SERVICE_NAME
    sleep 2
    show_status
}

show_logs() {
    echo -e "${BLUE}=== Hawwa Staging Logs ===${NC}"
    echo
    echo -e "${YELLOW}Error Log:${NC}"
    tail -f "$LOG_DIR/gunicorn_staging_error.log" &
    
    echo -e "${YELLOW}Access Log:${NC}"
    tail -f "$LOG_DIR/gunicorn_staging_access.log" &
    
    echo "Press Ctrl+C to stop following logs"
    wait
}

update_ssl() {
    echo -e "${YELLOW}Updating SSL Certificate...${NC}"
    certbot renew --nginx
    systemctl reload nginx
}

case "$1" in
    start)
        start_staging
        ;;
    stop)
        stop_staging
        ;;
    restart)
        restart_staging
        ;;
    reload)
        reload_staging
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    ssl)
        update_ssl
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|reload|status|logs|ssl}"
        echo
        echo "Commands:"
        echo "  start   - Start the staging environment"
        echo "  stop    - Stop the staging environment"
        echo "  restart - Restart the staging environment"
        echo "  reload  - Graceful reload (no downtime)"
        echo "  status  - Show detailed status"
        echo "  logs    - Follow live logs"
        echo "  ssl     - Update SSL certificate"
        echo
        exit 1
        ;;
esac

exit 0