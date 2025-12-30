#!/bin/bash

echo "🚀 Starting Magic Formula Stock Analysis Platform..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend .env file..."
    cp backend/.env.example backend/.env
fi

if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend .env file..."
    cp frontend/.env.example frontend/.env
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start all services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start (this may take 2-3 minutes)..."
echo ""

# Wait for Keycloak
echo "Waiting for Keycloak..."
timeout=180
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8081/health/ready > /dev/null 2>&1; then
        echo "✅ Keycloak is ready!"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "   Still waiting... ($elapsed seconds)"
done

# Wait for Backend
echo "Waiting for Backend..."
sleep 10
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is ready!"
else
    echo "⚠️  Backend may still be starting..."
fi

# Wait for Frontend
echo "Waiting for Frontend..."
sleep 5
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is ready!"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "=========================================="
echo "✨ Application is ready!"
echo "=========================================="
echo ""
echo "🌐 Frontend:        http://localhost:3000"
echo "🔧 Backend API:     http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo "🔐 Keycloak Admin:  http://localhost:8081"
echo ""
echo "=========================================="
echo "👤 Login Credentials"
echo "=========================================="
echo ""
echo "Demo User:"
echo "  Username: demo"
echo "  Password: demo123"
echo ""
echo "Admin User:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Keycloak Admin:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "=========================================="
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "Happy analyzing! 📈"
