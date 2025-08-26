#!/bin/bash

echo "🧪 Testing Claude Guardian Data Persistence"
echo "============================================"

# Test 1: Check current data state
echo "📊 Current Data State:"
echo "- Qdrant Collections: $(curl -s http://localhost:6333/collections | jq '.result.collections | length') collections"
echo "- PostgreSQL Tables: $(docker exec claude-guardian-postgres psql -U cguser -d claude_guardian -c "\dt" | grep -c "table")"
echo "- Redis Keys: $(docker exec claude-guardian-redis redis-cli DBSIZE | grep -o '[0-9]*')"

# Test 2: Restart containers and verify persistence
echo ""
echo "🔄 Restarting Containers to Test Persistence..."
docker restart claude-guardian-postgres claude-guardian-qdrant claude-guardian-redis

# Wait for startup
echo "⏳ Waiting for containers to restart..."
sleep 15

# Test 3: Verify data survived restart
echo ""
echo "✅ Post-Restart Data State:"
COLLECTIONS=$(curl -s http://localhost:6333/collections | jq '.result.collections | length')
TABLES=$(docker exec claude-guardian-postgres psql -U cguser -d claude_guardian -c "\dt" 2>/dev/null | grep -c "table" || echo "0")
REDIS_KEYS=$(docker exec claude-guardian-redis redis-cli DBSIZE 2>/dev/null | grep -o '[0-9]*' || echo "0")

echo "- Qdrant Collections: $COLLECTIONS collections"
echo "- PostgreSQL Tables: $TABLES tables"  
echo "- Redis Keys: $REDIS_KEYS keys"

# Test 4: Show actual collection names
echo ""
echo "📋 Persistent Qdrant Collections:"
curl -s http://localhost:6333/collections | jq '.result.collections[] | .name'

# Test 5: Show persistent directories
echo ""
echo "💾 Persistent Storage Directories:"
echo "$(du -sh ./data/* 2>/dev/null | sed 's|./data/|  |')"

if [ "$COLLECTIONS" -gt "0" ] && [ "$TABLES" -gt "0" ]; then
    echo ""
    echo "🎉 SUCCESS: Data persistence is working correctly!"
else
    echo ""
    echo "❌ ISSUE: Some data was not persisted properly"
fi