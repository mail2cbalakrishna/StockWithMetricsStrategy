#!/bin/bash

# Quick status check for stock fetching system

echo "=================================================="
echo "📊 Stock Analysis Platform - System Status"
echo "=================================================="
echo ""

# Check if containers are running
echo "🐳 Docker Status:"
BACKEND_STATUS=$(docker ps --filter "name=stock-analysis-backend" --format "{{.Status}}" 2>/dev/null)
if [ ! -z "$BACKEND_STATUS" ]; then
    echo "   ✅ Backend: $BACKEND_STATUS"
else
    echo "   ❌ Backend: NOT RUNNING"
    echo ""
    echo "Run: docker-compose up -d"
    exit 1
fi

echo ""

# Check API keys
echo "🔑 API Keys Configuration:"
ALPHA_KEY=$(docker exec stock-analysis-backend printenv ALPHA_VANTAGE_API_KEY 2>/dev/null)
POLYGON_KEY=$(docker exec stock-analysis-backend printenv POLYGON_API_KEY 2>/dev/null)

if [ "$ALPHA_KEY" != "demo" ] && [ ! -z "$ALPHA_KEY" ]; then
    echo "   ✅ Alpha Vantage: Configured"
    HAS_ALPHA=true
else
    echo "   ❌ Alpha Vantage: NOT configured (using 'demo')"
    HAS_ALPHA=false
fi

if [ ! -z "$POLYGON_KEY" ]; then
    echo "   ✅ Polygon.io: Configured"
    HAS_POLYGON=true
else
    echo "   ❌ Polygon.io: NOT configured"
    HAS_POLYGON=false
fi

echo ""

# Expected success rate
echo "📈 Expected Performance:"
if [ "$HAS_ALPHA" = true ] && [ "$HAS_POLYGON" = true ]; then
    echo "   Success Rate: 95-99%"
    echo "   Status: ✅✅ EXCELLENT"
elif [ "$HAS_ALPHA" = true ]; then
    echo "   Success Rate: 90-95%"
    echo "   Status: ✅ GOOD"
else
    echo "   Success Rate: 5-10%"
    echo "   Status: ❌ POOR (Yahoo Finance rate limited)"
fi

echo ""

# Check recent activity
echo "📊 Recent Activity:"
SUCCESSFUL=$(docker-compose logs backend 2>/dev/null | grep -c "✓.*Successfully fetched" || echo "0")
FALLBACK_AV=$(docker-compose logs backend 2>/dev/null | grep -c "alpha_vantage succeeded" || echo "0")
FALLBACK_PG=$(docker-compose logs backend 2>/dev/null | grep -c "polygon succeeded" || echo "0")
FAILED=$(docker-compose logs backend 2>/dev/null | grep -c "All sources failed" || echo "0")

echo "   Successful: $SUCCESSFUL stocks"
echo "   Alpha Vantage fallback: $FALLBACK_AV times"
echo "   Polygon fallback: $FALLBACK_PG times"
echo "   All sources failed: $FAILED times"

echo ""

# Check if processing is active
PROCESSING=$(docker-compose logs --tail=10 backend 2>/dev/null | grep -E "(Progress:|Starting parallel|completed)" | tail -1)
if [ ! -z "$PROCESSING" ]; then
    echo "🔄 Current Status:"
    echo "   $PROCESSING"
else
    echo "💤 Status: Idle (waiting for next refresh)"
fi

echo ""
echo "=================================================="
echo "💡 Quick Actions:"
echo "=================================================="
echo ""

if [ "$HAS_ALPHA" = false ] || [ "$HAS_POLYGON" = false ]; then
    echo "⚠️  Configure FREE API keys for better performance:"
    echo "   ./setup-api-keys.sh"
    echo ""
fi

echo "📺 View live logs:"
echo "   docker-compose logs -f backend"
echo ""
echo "🔄 Restart backend:"
echo "   docker-compose restart backend"
echo ""
echo "🌐 Open application:"
echo "   open http://localhost:3000"
echo ""
echo "=================================================="
