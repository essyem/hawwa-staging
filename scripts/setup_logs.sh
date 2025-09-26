#!/usr/bin/env bash
set -euo pipefail

# Create log directories and set ownership/permissions
LOG_DIRS=(/var/log/nginx /var/log/hawwa /home/azureuser/hawwa/logs)
for d in "${LOG_DIRS[@]}"; do
  sudo mkdir -p "$d"
  sudo chown azureuser:azureuser "$d"
  sudo chmod 750 "$d"
done

echo "Created log directories and set ownership to azureuser" 

echo "You may want to copy the logrotate config to /etc/logrotate.d/hawwa"
