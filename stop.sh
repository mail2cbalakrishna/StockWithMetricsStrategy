#!/bin/bash

echo "🛑 Stopping Magic Formula Stock Analysis Platform..."
echo ""

# Stop all containers
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "To start again, run: ./start.sh"
