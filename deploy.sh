#!/bin/bash
# Hawwa Wellness Deployment Script
# This script handles deployment, service management, and maintenance tasks

HAWWA_DIR="/home/azureuser/hawwa"
VENV_DIR="$HAWWA_DIR/env-hawwa"
SERVICE_NAME="hawwa.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if service is running
check_service() {
    systemctl is-active --quiet $SERVICE_NAME
    return $?
}

# Function to deploy the application
deploy() {
    log "Starting Hawwa Wellness deployment..."
    
    cd $HAWWA_DIR
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Pull latest code (if using git)
    if [ -d ".git" ]; then
        log "Pulling latest code from repository..."
        git pull origin master
    fi
    
    # Install/update dependencies
    log "Installing/updating dependencies..."
    pip install -r requirements.txt
    
    # Run migrations
    log "Running database migrations..."
    python manage.py migrate
    
    # Collect static files
    log "Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Create superuser if needed (interactive)
    read -p "Create/update superuser? (y/N): " create_user
    if [ "$create_user" = "y" ] || [ "$create_user" = "Y" ]; then
        python manage.py createsuperuser
    fi
    
    # Restart services
    log "Restarting services..."
    sudo systemctl daemon-reload
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl restart nginx
    
    # Check service status
    if check_service; then
        log "Deployment completed successfully!"
        log "Hawwa service is running"
    else
        error "Deployment failed - service is not running"
        return 1
    fi
}

# Function to start services
start_services() {
    log "Starting Hawwa services..."
    sudo systemctl start $SERVICE_NAME
    sudo systemctl start nginx
    
    if check_service; then
        log "Services started successfully"
    else
        error "Failed to start services"
        return 1
    fi
}

# Function to stop services
stop_services() {
    log "Stopping Hawwa services..."
    sudo systemctl stop $SERVICE_NAME
    log "Services stopped"
}

# Function to restart services
restart_services() {
    log "Restarting Hawwa services..."
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl reload nginx
    
    if check_service; then
        log "Services restarted successfully"
    else
        error "Failed to restart services"
        return 1
    fi
}

# Function to check service status
status() {
    info "=== Hawwa Service Status ==="
    systemctl status $SERVICE_NAME --no-pager
    echo ""
    
    info "=== Nginx Status ==="
    systemctl status nginx --no-pager
    echo ""
    
    info "=== Recent Logs ==="
    sudo tail -n 20 $HAWWA_DIR/logs/gunicorn_error.log
}

# Function to view logs
logs() {
    log_type=${1:-"error"}
    
    case $log_type in
        "access")
            sudo tail -f $HAWWA_DIR/logs/gunicorn_access.log
            ;;
        "error")
            sudo tail -f $HAWWA_DIR/logs/gunicorn_error.log
            ;;
        "nginx")
            sudo tail -f /var/log/nginx/hawwa_error.log
            ;;
        "django")
            tail -f $HAWWA_DIR/logs/django_debug.log
            ;;
        *)
            echo "Available log types: access, error, nginx, django"
            ;;
    esac
}

# Function to backup database
backup_db() {
    backup_dir="$HAWWA_DIR/backups"
    mkdir -p $backup_dir
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="$backup_dir/hawwa_db_backup_$timestamp.sql"
    
    log "Creating database backup..."
    pg_dump -h localhost -U dbadmin -d hawwa_db > $backup_file
    
    if [ $? -eq 0 ]; then
        log "Database backup created: $backup_file"
    else
        error "Database backup failed"
        return 1
    fi
}

# Function to setup SSL
setup_ssl() {
    log "Running SSL setup script..."
    $HAWWA_DIR/setup_ssl.sh
}

# Function to update production secret key
update_secret_key() {
    new_key=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    warn "Current secret key in hawwa.service will be replaced!"
    echo "New secret key: $new_key"
    read -p "Update secret key? (y/N): " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        sudo sed -i "s/Environment=HAWWA_SECRET_KEY=.*/Environment=HAWWA_SECRET_KEY=$new_key/" /etc/systemd/system/$SERVICE_NAME
        sudo systemctl daemon-reload
        log "Secret key updated. Restart the service to apply changes."
    fi
}

# Function to show help
show_help() {
    echo "Hawwa Wellness Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy          Full deployment (pull, install, migrate, restart)"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show service status and recent logs"
    echo "  logs [type]     Show logs (access, error, nginx, django)"
    echo "  backup          Create database backup"
    echo "  ssl             Setup SSL certificates"
    echo "  secret          Generate and update secret key"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 logs error"
    echo "  $0 status"
}

# Main script logic
case ${1:-help} in
    "deploy")
        deploy
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        status
        ;;
    "logs")
        logs $2
        ;;
    "backup")
        backup_db
        ;;
    "ssl")
        setup_ssl
        ;;
    "secret")
        update_secret_key
        ;;
    "help"|*)
        show_help
        ;;
esac