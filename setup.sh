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
# Try to install the modern plugin, fallback to classic if needed
sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose

# 3. Setup the Auto-Start Service
if [ -f "molly-wizard.service" ]; then
    echo "[INFO] Configuring Setup Wizard to start on boot..."
    sudo cp molly-wizard.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable molly-wizard.service
    sudo systemctl start molly-wizard.service
else
    echo "[ERROR] molly-wizard.service NOT FOUND in $PROJECT_DIR"
    echo "Check your filename and try again."
    exit 1
fi

# 4. Provide the URL
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "------------------------------------------------------"
echo "SETUP WIZARD IS LIVE"
echo "Please open your browser and go to:"
echo "http://$IP_ADDR  OR  http://$(hostname).local"
echo "------------------------------------------------------"

# 5. Wait for the .env file
echo "[INFO] Waiting for web configuration to complete..."
while [ ! -f .env ]
do
  sleep 5
done

# 6. Bring up the Docker Stack
echo "[INFO] Credentials received. Starting services..."
sudo docker compose up -d || sudo docker-compose up -d

echo "[SUCCESS] Gateway is now running!"