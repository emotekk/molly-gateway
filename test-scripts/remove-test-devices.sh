#!/bin/bash
# remove-test-devices.sh - Remove mock test devices from database

echo "=== Removing Test Devices ==="
echo ""

if [ ! -f "./data/mollysocket.db" ]; then
    echo "❌ Database not found"
    exit 1
fi

# Remove all test devices
sudo docker exec molly-socket sqlite3 /data/mollysocket.db << 'EOF'
DELETE FROM connections WHERE uuid LIKE 'test-device-%';
EOF

echo "✅ Test devices removed"
echo ""

# Show remaining devices
REMAINING=$(sudo docker exec molly-socket sqlite3 /data/mollysocket.db "SELECT COUNT(*) FROM connections;")

echo "📊 Remaining devices: $REMAINING"

if [ "$REMAINING" -gt 0 ]; then
    echo ""
    echo "Remaining devices:"
    sudo docker exec molly-socket sqlite3 /data/mollysocket.db "SELECT uuid, device_id FROM connections;"
fi

echo ""
echo "Dashboard should now show only real registered devices."
