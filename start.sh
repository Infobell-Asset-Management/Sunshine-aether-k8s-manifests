#!/bin/bash

# Asset Track Application Startup Script
echo "🚀 Starting Asset Track Application..."

# Navigate to the infra directory
cd "$(dirname "$0")/infra"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start all services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ Asset Track Application is starting up!"
echo ""
echo "📊 Services:"
echo "   • Web UI: http://localhost:3000"
echo "   • API: http://localhost:8000"
echo "   • RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "   • PostgreSQL: localhost:5432"
echo ""
echo "📋 Service Ports:"
echo "   • Agent Service: 8005"
echo "   • Collector Service: 8002"
echo "   • Processor Service: 8001"
echo "   • API Service: 8000"
echo "   • Web UI: 3000"
echo ""
echo "🛑 To stop the application: ./stop.sh"
echo "📝 To view logs: docker-compose logs -f [service-name]"
