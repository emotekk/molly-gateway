#!/bin/bash

# Ensure we are in the project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "[INFO] Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

echo "[INFO] Installing Python dependencies..."
sudo apt-get install -y python3-pip python3-flask curl

# 1. Install Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "[INFO] Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo systemctl enable --now tailscaled
else
    echo "[INFO] Tailscale already installed."
fi

# 2. Install Docker & Docker Compose
echo "[INFO] Installing Docker..."
sudo apt-get install -y docker.io

# Attempt to install Docker Compose through various package names
echo "[INFO] Installing Docker Compose..."
sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose || sudo pip3 install docker-compose

# 3. Setup the Auto-Start Service
# This checks for the filename you chose: molly-wizard.service
SERVICE_FILE="molly-wizard.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "[INFO] Configuring $SERVICE_FILE to start on boot..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_FILE"
    sudo systemctl start "$SERVICE_FILE"
else
    echo "[ERROR] $SERVICE_FILE NOT FOUND in $PROJECT_DIR"
    echo "Please check your filename and try again."
    exit 1
fi

# 4. Provide the Web Configuration URL
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "------------------------------------------------------"
echo "SETUP WIZARD IS LIVE"
echo "Please open your browser and go to:"
echo "URL 1: http://$IP_ADDR"
echo "URL 2: http://$(hostname).local"
echo "------------------------------------------------------"

# 5. Wait for the .env file to be created by the Wizard
echo "[INFO] Waiting for web configuration to complete..."
while [ ! -f .env ]
do
  sleep 5
done

# 6. Bring up the Docker Stack
echo "[INFO] Credentials received. Starting services..."
# Support both 'docker compose' (v2) and 'docker-compose' (v1)
sudo docker compose up -d || sudo docker-compose up -d

echo "[SUCCESS] Gateway is now running!"