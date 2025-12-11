#!/bin/bash

echo "🛑 Stopping Roach Parlor services..."

# Stop development services if running
docker-compose -f docker-compose.dev.yml down 2>/dev/null

# Stop production services if running
docker-compose down 2>/dev/null

echo "✅ All services stopped"