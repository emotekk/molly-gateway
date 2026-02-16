#!/bin/bash

# Ensure we are in the project directory 
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "[INFO] Updating system and installing dependencies..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-flask curl docker.io docker-compose tailscale

# Create templates directory if it doesn't exist
mkdir -p templates

# 1. Optimize Network stack
echo "[INFO] Configuring network interfaces..."
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -P FORWARD ACCEPT
sudo iptables -I INPUT -i tailscale0 -j ACCEPT

# 2. Setup Systemd Service
SERVICE_FILE="molly-wizard.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "[INFO] Registering $SERVICE_FILE..."
    # Replace template paths with absolute paths
    sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_DIR|g" "$SERVICE_FILE"
    sudo sed -i "s|ExecStart=.*|ExecStart=/usr/bin/python3 $PROJECT_DIR/wizard.py|g" "$SERVICE_FILE"

    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_FILE"
    sudo systemctl start "$SERVICE_FILE"
else
    echo "[ERROR] $SERVICE_FILE not found."
    exit 1
fi

# 3. Output access info
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "------------------------------------------------------"
echo "INSTALLATION COMPLETE"
echo "Open your browser to: http://$IP_ADDR"
echo "------------------------------------------------------"