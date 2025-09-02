#!/bin/bash

# Asset Track Application Stop Script
echo "🛑 Stopping Asset Track Application..."

# Navigate to the infra directory
cd "$(dirname "$0")/infra"

# Stop all containers
echo "⏹️  Stopping containers..."
docker-compose down

# Remove containers and networks (optional)
read -p "Do you want to remove containers and networks? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing containers and networks..."
    docker-compose down --remove-orphans
fi

echo "✅ Application stopped successfully!"
