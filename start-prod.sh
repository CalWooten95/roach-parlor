#!/bin/bash

echo "🚀 Starting Roach Parlor production environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ./setup.sh first."
    exit 1
fi

# Start production services
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Production environment started successfully!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"
else
    echo "❌ Failed to start production environment"
    exit 1
fi