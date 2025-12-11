#!/bin/bash

# Roach Parlor Setup Script
echo "🚀 Setting up Roach Parlor Betting Tracker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose detected"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and update the following:"
    echo "   - POSTGRES_PASSWORD (set a secure password)"
    echo "   - SESSION_SECRET (generate a random string)"
    echo "   - ADMIN_PASSWORD (set admin password)"
    echo "   - ADMIN_ACCESS_KEY (generate a random key)"
    echo "   - DISCORD_TOKEN (if using Discord bot)"
    echo "   - OPENAI_API_KEY (if using Discord bot)"
    echo ""
    read -p "Press Enter after updating .env file to continue..."
else
    echo "ℹ️  .env file already exists"
fi

# Create frontend .env file if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend .env file..."
    cp frontend/.env.example frontend/.env
    echo "✅ Frontend .env file created"
else
    echo "ℹ️  Frontend .env file already exists"
fi

echo ""
echo "🐳 Building Docker containers..."
docker-compose -f docker-compose.dev.yml build

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker containers"
    exit 1
fi

echo "✅ Docker containers built successfully"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Available commands:"
echo "   ./start-dev.sh       - Start development environment"
echo "   ./start-prod.sh      - Start production environment"
echo "   ./stop.sh            - Stop all services"
echo "   ./logs.sh            - View logs"
echo ""
echo "🚀 To start development:"
echo "   ./start-dev.sh"
echo ""
echo "🌐 Once started, access:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Database: localhost:5432"