# 🛡️ Molly Gateway

**Private push notifications for de-Googled Android devices**

A plug-and-play notification bridge for [Molly](https://molly.im/) (hardened Signal fork) that works without Google Play Services. Run on a Raspberry Pi or any Linux server to receive Signal notifications privately through your own infrastructure.

---

## 🎯 What Is This?

Molly Gateway is a self-hosted notification server that:
- ✅ Enables push notifications for Molly without Google Play Services
- ✅ Works on de-Googled Android (GrapheneOS, CalyxOS, LineageOS, etc.)
- ✅ Routes notifications through your own hardware (Raspberry Pi, VPS, etc.)
- ✅ Uses Tailscale for secure remote access
- ✅ Zero cloud dependencies after setup
- ✅ Fully private - your data never touches third-party servers

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────┐
│                    How It Works                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│  Signal Server                                        │
│       ↓                                               │
│  Your Gateway (Raspberry Pi)                          │
│       ↓                                               │
│  Tailscale Network (For remote access)                │
│       ↓                                               │
│  Your Phone (Molly app + Tailscale)                   │
│       ↓                                               │
│  You get notified!                                    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

```
Signal → Your Pi → Tailscale → Your Phone → Notification 🔔
```

- **At Home:** Tailscale uses direct peer-to-peer over WiFi (fast!)  
- **Away:** Tailscale routes through encrypted relay servers (secure!)
- **Always:** Private - your data, your hardware

---

**Important:** Tailscale must stay enabled on your phone at all times, but it's smart enough to use direct local connections when you're at home for maximum speed with minimal battery drain.

---

## ⚡ Quick Start

### What You Need
- Raspberry Pi (3B or newer)
- [Tailscale account](https://tailscale.com/) (free)
- Molly app on Android

### 📦 What Gets Installed

- **Docker & Docker Compose** - Runs MollySocket container
- **Tailscale** - Creates secure VPN tunnel
- **Python + Flask** - Powers web setup wizard
- **MollySocket** - Handles push notifications

### Installation (10 minutes)

```bash
# 1. Download and run setup
git clone https://github.com/emotekk/molly-gateway.git
cd molly-gateway
chmod +x setup.sh
sudo ./setup.sh

# 2. Open browser to your Pi's IP (shown after setup)
# 3. Enter Tailscale auth key from https://login.tailscale.com/admin/settings/keys
# 4. Wait 2-3 minutes for deployment
# 5. Done!
```
All dependencies (Docker, Tailscale, Python) are installed automatically.


### Connect Your Phone

1. Install Tailscale on your Android phone
2. Log in with same Tailscale account
3. Keep Tailscale running
4. Open Molly → Settings → Notifications → UnifiedPush → Register
5. Enter gateway URL from dashboard
6. Scan QR code
7. ✅ Notifications working!

---



## 🔧 Management

### View Dashboard
```bash
# Open browser to:
http://<your-pi-ip>
```

### View Logs
```bash
sudo docker logs molly-socket
```

### Restart Gateway
```bash
sudo docker-compose restart
```

### Complete Reset
```bash
sudo docker-compose down
rm .env
rm -rf data
sudo systemctl restart molly-wizard.service
```

---

## ❓ Common Issues

### "VAPID Key not found" error
```bash
# Delete config and run setup again
sudo docker-compose down
rm .env
sudo systemctl restart molly-wizard.service
```

### Can't access from phone
- ✅ Is Tailscale running on phone?
- ✅ Same Tailscale account on Pi and phone?
- ✅ Gateway container running? `sudo docker ps`

### Notifications not working
- Check Molly → Settings → Notifications → UnifiedPush shows "Registered"
- Disable battery optimization for Molly and Tailscale
- View gateway logs: `sudo docker logs -f molly-socket`

---

## 🔐 Security

- ✅ Signal messages remain end-to-end encrypted
- ✅ Tailscale provides encrypted tunnel
- ✅ VAPID keys never leave your Pi
- ✅ No third-party cloud services

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

**Built with:**
- [MollySocket](https://github.com/mollyim/mollysocket) - Notification engine
- [Molly](https://molly.im/) - Hardened Signal fork
- [Tailscale](https://tailscale.com/) - Zero-config VPN


---

*Made with ❤️ for the privacy community*