🚀 Molly-Pi Gateway

Molly-Pi is a "plug-and-play" notification bridge designed for privacy-conscious users running Molly (the hardened Signal fork) on de-Googled Android devices.

The goal of this project is to provide a reliable, battery-efficient alternative to Google's Firebase Cloud Messaging (FCM). By hosting your own gateway, you get instant notifications via UnifiedPush without needing Google Play Services or constant background battery drain.
✨ Features

    Mobile-Friendly Setup: A clean web-based wizard to configure your gateway from your phone.

    Tailscale Integrated: Secure, "zero-config" networking. Access your gateway on 5G without opening router ports.

    Hardware Agnostic: Optimized for Raspberry Pi 3/4/5 and Zero 2W, but runs on any Linux PC via Docker.

    Headless Operation: Designed to run without a monitor or keyboard—just plug into your router and go.

🛠️ The Stack

    MollySocket: The core bridge between Signal and UnifiedPush.

    Nginx Proxy Manager: Handles SSL and local routing.

    Tailscale: Provides a secure tunnel to your phone.

    Docker: Ensures the services are isolated and easy to update.

📥 Installation
Method 1: The "Appliance" Way (Recommended for Pi users)

Coming Soon: Pre-baked SD Card Images!
Method 2: The Scripted Install (For any Debian/Ubuntu system)

    Install a clean version of Raspberry Pi OS Lite (64-bit) or any Debian-based Linux.

    Clone this repository: git clone https://github.com/emotekk/molly-gateway.git cd molly-gateway

    Run the setup script: chmod +x setup.sh ./setup.sh

⚙️ Configuration

Once the script is running:

    Open your phone's browser and go to http://molly-pi.local (or the IP address of your device).

    Enter your Tailscale Auth Key (found in your Tailscale Admin Console).

    Choose a Device Name.

    Click Activate.

Your gateway will automatically start the Docker services. You can then link your Molly app to the gateway using the UnifiedPush settings in the app.

📄 License

This project is licensed under the MIT License.