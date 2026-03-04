#!/bin/bash
# check-mollysocket-db.sh - Inspect MollySocket's database structure

echo "=== MollySocket Database Inspector ==="
echo ""

# Check if database exists
if [ ! -f "./data/mollysocket.db" ]; then
    echo "❌ Database not found at ./data/mollysocket.db"
    echo ""
    echo "This means either:"
    echo "1. No devices have registered yet"
    echo "2. Database path is different"
    echo "3. MollySocket container isn't running"
    echo ""
    echo "Please register at least one device first."
    exit 1
fi

echo "✅ Database found!"
echo ""

# Show tables
echo "📋 Tables in database:"
sudo docker exec molly-socket sqlite3 /data/mollysocket.db ".tables"
echo ""

# Show schema for each table
echo "🔍 Database schema:"
sudo docker exec molly-socket sqlite3 /data/mollysocket.db ".schema"
echo ""

# Show sample data (first row from each table)
echo "📊 Sample data from each table:"
for table in $(sudo docker exec molly-socket sqlite3 /data/mollysocket.db ".tables"); do
    echo ""
    echo "--- Table: $table ---"
    sudo docker exec molly-socket sqlite3 /data/mollysocket.db "SELECT * FROM $table LIMIT 1;"
done

echo ""
echo "=== End of inspection ==="
echo ""
echo "💡 If the schema is different from what wizard.py expects,"
echo "   you'll need to update the get_devices() function in wizard.py"
