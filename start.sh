#!/bin/bash

# GymApp Docker Quick Start Script

set -e

echo "🏋️  Starting GymApp Docker Environment..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from env.example..."
    
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your API keys before continuing!"
        echo "   - GOOGLE_PLACES_API_KEY"
        echo "   - VITE_GOOGLE_MAPS_API_KEY"
        echo ""
        read -p "Press Enter when you've updated .env with your API keys..."
    else
        echo "❌ env.example not found!"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Clean up any orphaned networks (optional - uncomment if you have network issues)
# docker network prune -f > /dev/null 2>&1

# Parse command line arguments
MODE=${1:-dev}

if [ "$MODE" == "prod" ]; then
    echo "🚀 Starting in PRODUCTION mode..."
    docker compose -f docker-compose.prod.yml up --build -d
    echo ""
    echo "✅ Production environment started!"
    echo ""
    echo "📊 Services:"
    echo "   Frontend:  http://localhost (port 80)"
    echo "   Backend:   http://localhost/api/"
    echo "   Database:  localhost:5432"
    echo ""
    echo "📝 View logs:"
    echo "   docker compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo "🛑 Stop:"
    echo "   docker compose -f docker-compose.prod.yml down"
    
elif [ "$MODE" == "dev" ]; then
    echo "🔧 Starting in DEVELOPMENT mode..."
    # Stop any existing containers first to avoid network conflicts
    docker compose --profile dev down 2>/dev/null || true
    docker compose --profile dev up --build
    
else
    echo "❌ Invalid mode: $MODE"
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
fi

