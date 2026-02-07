#!/bin/bash

# Ensure we are in the project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "[INFO] Updating system and installing dependencies..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io python3-pip python3-flask curl

# 1. Install Tailscale using official script
echo "[INFO] Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled

# 2. Install Docker Compose V2 plugin
echo "[INFO] Installing Docker Compose..."
sudo apt-get install -y docker-compose-plugin

# 3. Setup the Auto-Start Service
echo "[INFO] Configuring Setup Wizard to start on boot..."
sudo cp molly-pi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable molly-pi.service

# 4. Launch the Setup Wizard
echo "[INFO] Launching Molly-Pi Setup Wizard..."
echo "Access the wizard at: http://$(hostname).local"
sudo systemctl start molly-pi.service

# 5. Wait for the .env file to be created by the Wizard
echo "[WAIT] Waiting for web configuration to complete..."
while [ ! -f .env ]
do
  sleep 5
done

# 6. Bring up the Docker Stack
echo "[OK] Credentials received. Starting Molly-Pi services..."
sudo docker compose up -d

echo "[SUCCESS] Molly-Pi is now running and configured."