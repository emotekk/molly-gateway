#!/bin/bash
# diagnose-remote.sh - Debug why remote IP:8080 doesn't work

echo "=== Remote Connection Diagnostics ==="
echo ""

# 1. Check Tailscale status
echo "1️⃣  Tailscale Status:"
sudo tailscale status
echo ""

# 2. Check if MollySocket is listening
echo "2️⃣  Is MollySocket listening on port 8080?"
sudo ss -tulpn | grep :8080
echo ""

# 3. Check container status
echo "3️⃣  Container Status:"
sudo docker ps | grep molly-socket
echo ""

# 4. Check .env configuration
echo "4️⃣  Configuration (.env):"
if [ -f .env ]; then
    cat .env
else
    echo "❌ .env file not found!"
fi
echo ""

# 5. Test local connection
echo "5️⃣  Testing local connection (localhost:8080):"
curl -I http://localhost:8080 2>&1 | head -5
echo ""

# 6. Get Tailscale IP
echo "6️⃣  Your Tailscale IP:"
TAILSCALE_IP=$(tailscale ip -4)
echo "   $TAILSCALE_IP"
echo ""

# 7. Test Tailscale connection from Pi itself
echo "7️⃣  Testing Tailscale connection from Pi:"
curl -I http://$TAILSCALE_IP:8080 2>&1 | head -5
echo ""

# 8. Check firewall rules
echo "8️⃣  Firewall rules for Tailscale:"
sudo iptables -L INPUT -n | grep tailscale
echo ""

# 9. Check MollySocket logs
echo "9️⃣  MollySocket logs (last 10 lines):"
sudo docker logs --tail 10 molly-socket
echo ""

# 10. Recommendations
echo "🔧 DIAGNOSIS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if port is listening
PORT_LISTENING=$(sudo ss -tulpn | grep :8080 | wc -l)
if [ "$PORT_LISTENING" -eq 0 ]; then
    echo "❌ MollySocket is NOT listening on port 8080"
    echo ""
    echo "Possible fixes:"
    echo "  1. Check container logs: sudo docker logs molly-socket"
    echo "  2. Restart container: sudo docker-compose restart"
    echo "  3. Check .env file has correct MOLLY_ALLOWED_ENDPOINTS=[\"*\"]"
else
    echo "✅ MollySocket IS listening on port 8080"
fi

echo ""

# Check localhost works
LOCAL_WORKS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null)
if [ "$LOCAL_WORKS" = "200" ] || [ "$LOCAL_WORKS" = "404" ]; then
    echo "✅ Local connection works (http://localhost:8080)"
else
    echo "❌ Local connection FAILS (http://localhost:8080)"
    echo ""
    echo "Possible fixes:"
    echo "  1. Container may not be fully started"
    echo "  2. Check: sudo docker ps"
    echo "  3. Check: sudo docker logs molly-socket"
fi

echo ""

# Check Tailscale connection
if [ -n "$TAILSCALE_IP" ]; then
    TS_WORKS=$(curl -s -o /dev/null -w "%{http_code}" http://$TAILSCALE_IP:8080 2>/dev/null)
    if [ "$TS_WORKS" = "200" ] || [ "$TS_WORKS" = "404" ]; then
        echo "✅ Tailscale connection works from Pi (http://$TAILSCALE_IP:8080)"
        echo ""
        echo "📱 To test from another device:"
        echo "   1. Install Tailscale on your phone/computer"
        echo "   2. Login to same Tailscale account"
        echo "   3. Open: http://$TAILSCALE_IP:8080"
        echo ""
        echo "If it still doesn't work from other devices:"
        echo "   - Make sure other device is connected to Tailscale"
        echo "   - Check: tailscale status (on other device)"
        echo "   - Try: tailscale ping $TAILSCALE_IP (from other device)"
    else
        echo "❌ Tailscale connection FAILS from Pi"
        echo ""
        echo "Possible fixes:"
        echo "  1. Firewall blocking Tailscale"
        echo "  2. Run: sudo iptables -I INPUT -i tailscale0 -j ACCEPT"
        echo "  3. Check: sudo tailscale status"
        echo "  4. Reconnect: sudo tailscale down && sudo tailscale up"
    fi
else
    echo "❌ Tailscale IP not found"
    echo ""
    echo "Fix:"
    echo "  sudo tailscale up --authkey=YOUR_KEY --accept-routes"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Quick Test:"
echo "   From another device on Tailscale, try:"
echo "   curl -I http://$TAILSCALE_IP:8080"
echo ""
echo "   If that works, your remote connection is fine!"