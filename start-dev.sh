#!/bin/bash

echo "🚀 Starting Roach Parlor development environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ./setup.sh first."
    exit 1
fi

# Start development services
docker-compose -f docker-compose.dev.yml up -d

if [ $? -eq 0 ]; then
    echo "✅ Development environment started successfully!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   Database: localhost:5432"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose -f docker-compose.dev.yml logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose -f docker-compose.dev.yml down"
else
    echo "❌ Failed to start development environment"
    exit 1
fi