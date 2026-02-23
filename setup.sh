#!/bin/bash

# Exit on any error
set -e

# Ensure we are in the project directory 
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "[INFO] Molly Gateway Setup Starting..."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "[ERROR] Please run this script as a normal user (not root)"
    echo "Usage: ./setup.sh"
    exit 1
fi

# 1. Update package lists (required before installing)
echo "[INFO] Updating package lists..."
sudo apt-get update

# 2. Install basic dependencies
echo "[INFO] Installing basic dependencies..."
sudo apt-get install -y \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    iptables \
    python3 \
    python3-pip \
    python3-flask

# 3. Stop and disable Apache2 if running (conflicts with wizard on port 80)
if systemctl is-active --quiet apache2; then
    echo "[INFO] Apache2 is running on port 80. Stopping it..."
    sudo systemctl stop apache2
    sudo systemctl disable apache2
    echo "[INFO] Apache2 stopped and disabled"
fi

# 4. Install Docker
if ! command -v docker &> /dev/null; then
    echo "[INFO] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "[INFO] Docker installed"
else
    echo "[INFO] Docker already installed"
fi

# 5. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[INFO] Installing Docker Compose..."
    sudo apt-get install -y docker-compose
    echo "[INFO] Docker Compose installed"
else
    echo "[INFO] Docker Compose already installed"
fi

# 6. Install Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "[INFO] Installing Tailscale..."
    
    # Add Tailscale's package signing key and repository
    curl -fsSL https://pkgs.tailscale.com/stable/debian/$(lsb_release -cs).noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
    curl -fsSL https://pkgs.tailscale.com/stable/debian/$(lsb_release -cs).tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
    
    # Update package list and install
    sudo apt-get update
    sudo apt-get install -y tailscale
    
    echo "[INFO] Tailscale installed"
else
    echo "[INFO] Tailscale already installed"
fi

# 7. Create templates directory
echo "[INFO] Setting up application directories..."
mkdir -p templates

# 8. Optimize Network stack
echo "[INFO] Configuring network interfaces..."
sudo sysctl -w net.ipv4.ip_forward=1

# Make it persistent
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
fi

# Configure firewall
sudo iptables -P FORWARD ACCEPT
sudo iptables -I INPUT -i tailscale0 -j ACCEPT 2>/dev/null || true

# 9. Setup Systemd Service
SERVICE_FILE="molly-wizard.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "[INFO] Registering $SERVICE_FILE..."
    
    # Replace template paths with absolute paths
    sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_DIR|g" "$SERVICE_FILE"
    sudo sed -i "s|ExecStart=.*|ExecStart=/usr/bin/python3 $PROJECT_DIR/wizard.py|g" "$SERVICE_FILE"

    # Copy service file
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_FILE"
    sudo systemctl start "$SERVICE_FILE"
    
    echo "[INFO] Service registered and started"
else
    echo "[ERROR] $SERVICE_FILE not found in $PROJECT_DIR"
    exit 1
fi

# 10. Wait a moment for service to start
sleep 2

# 11. Check if service is running
if systemctl is-active --quiet molly-wizard.service; then
    echo "[SUCCESS] Molly Gateway wizard is running!"
else
    echo "[WARNING] Service may not have started properly"
    echo "Check logs with: sudo journalctl -u molly-wizard.service -f"
fi

# 12. Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo "======================================================"
echo "         INSTALLATION COMPLETE!"
echo "======================================================"
echo ""
echo "Next steps:"
echo "  1. Open your browser to: http://$IP_ADDR"
echo "  2. Get a Tailscale auth key from:"
echo "     https://login.tailscale.com/admin/settings/keys"
echo "  3. Follow the setup wizard in your browser"
echo ""
echo "Troubleshooting:"
echo "  - View logs: sudo journalctl -u molly-wizard.service -f"
echo "  - Restart wizard: sudo systemctl restart molly-wizard.service"
echo "  - Check status: sudo systemctl status molly-wizard.service"
echo ""
echo "======================================================"