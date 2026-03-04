#!/bin/bash
# add-test-devices.sh - Add mock devices for testing dashboard

echo "=== Adding Test Devices to MollySocket Database ==="
echo ""

# Check if database exists, if not create it
if [ ! -f "./data/mollysocket.db" ]; then
    echo "⚠️  Database doesn't exist. Creating it first..."
    mkdir -p ./data
    
    # Create database with schema
    sudo docker exec molly-socket sqlite3 /data/mollysocket.db << 'EOF'
CREATE TABLE IF NOT EXISTS connections (
    uuid TEXT PRIMARY KEY,
    device_id TEXT,
    endpoint TEXT NOT NULL,
    created INTEGER NOT NULL,
    last_ping INTEGER
);
EOF
    echo "✅ Database created"
fi

echo "📱 Adding test devices..."

# Get current timestamp
CURRENT_TIME=$(date +%s)
ONE_HOUR_AGO=$((CURRENT_TIME - 3600))
ONE_DAY_AGO=$((CURRENT_TIME - 86400))

# Add test device 1 (Alice's Phone)
sudo docker exec molly-socket sqlite3 /data/mollysocket.db << EOF
INSERT OR REPLACE INTO connections (uuid, device_id, endpoint, created, last_ping)
VALUES (
    'test-device-alice-001',
    'Alice Phone',
    '/up/test-device-alice-001',
    $ONE_DAY_AGO,
    $CURRENT_TIME
);
EOF

# Add test device 2 (Bob's Phone)
sudo docker exec molly-socket sqlite3 /data/mollysocket.db << EOF
INSERT OR REPLACE INTO connections (uuid, device_id, endpoint, created, last_ping)
VALUES (
    'test-device-bob-002',
    'Bob Phone',
    '/up/test-device-bob-002',
    $ONE_HOUR_AGO,
    $CURRENT_TIME
);
EOF

# Add test device 3 (Carol's Tablet)
sudo docker exec molly-socket sqlite3 /data/mollysocket.db << EOF
INSERT OR REPLACE INTO connections (uuid, device_id, endpoint, created, last_ping)
VALUES (
    'test-device-carol-003',
    'Carol Tablet',
    '/up/test-device-carol-003',
    $CURRENT_TIME,
    $CURRENT_TIME
);
EOF

echo "✅ Test devices added!"
echo ""

# Verify they were added
echo "📋 Current devices in database:"
sudo docker exec molly-socket sqlite3 /data/mollysocket.db "SELECT uuid, device_id, endpoint FROM connections;"

echo ""
echo "🎉 Success! Now open your dashboard to see the test devices."
echo ""
echo "Dashboard URL: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "You can now test:"
echo "  - Device list display"
echo "  - Device count"
echo "  - Remove device functionality"
echo "  - Auto-refresh"
echo ""
echo "To remove test devices, run: ./remove-test-devices.sh"
