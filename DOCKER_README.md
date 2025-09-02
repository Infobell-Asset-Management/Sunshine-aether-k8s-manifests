# Asset Track Application - Docker Setup

This document explains how to run the Asset Track application using Docker Compose.

## 🏗️ Architecture

The application consists of the following microservices:

- **Agent Service** (Port 8005): Collects system metrics and publishes to RabbitMQ
- **Collector Service** (Port 8002): Consumes events from RabbitMQ
- **Processor Service** (Port 8001): Processes events and stores in PostgreSQL
- **API Service** (Port 8000): REST API for the frontend
- **Web UI** (Port 3000): React frontend application
- **PostgreSQL** (Port 5432): Database
- **RabbitMQ** (Ports 5672, 15672): Message queue

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 3000, 8000, 8001, 8002, 8005, 5432, 5672, 15672 available

### Start the Application

```bash
# From the aether-apps directory
./start.sh
```

Or manually:

```bash
cd infra
docker-compose up --build -d
```

### Stop the Application

```bash
# From the aether-apps directory
./stop.sh
```

Or manually:

```bash
cd infra
docker-compose down
```

## 📊 Access Points

Once started, you can access:

- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `infra` directory:

```env
# Database
DB_USER=assettrack
DB_PASSWORD=assettrack

# RabbitMQ
MQ_USER=guest
MQ_PASSWORD=guest

# Agent Configuration
NODE_ID=local-dev
PUBLISH_INTERVAL_SECONDS=3600
```

### Service Configuration

Each service can be configured via environment variables in `docker-compose.yml`:

- **Agent Service**: `NODE_ID`, `PUBLISH_INTERVAL_SECONDS`
- **Processor Service**: Database connection settings
- **API Service**: Service URLs for processor and collector

## 📝 Useful Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-service
docker-compose logs -f agent-service
docker-compose logs -f collector-service
docker-compose logs -f processor-service
docker-compose logs -f webapp-ui
```

### Check Service Status

```bash
docker-compose ps
```

### Rebuild a Specific Service

```bash
docker-compose build api-service
docker-compose up -d api-service
```

### Access Service Shell

```bash
docker-compose exec api-service bash
docker-compose exec processor-service bash
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo lsof -i :3000
   
   # Kill the process
   sudo kill -9 <PID>
   ```

2. **Docker Build Fails**
   ```bash
   # Clean up Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker-compose build --no-cache
   ```

3. **Services Not Starting**
   ```bash
   # Check service logs
   docker-compose logs <service-name>
   
   # Check service health
   docker-compose ps
   ```

4. **Database Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose exec postgres pg_isready -U assettrack
   
   # Check database logs
   docker-compose logs postgres
   ```

### Health Checks

All services include health checks. You can monitor them:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect <container-name> | grep -A 10 "Health"
```

## 🔄 Development Workflow

### Making Changes

1. **Code Changes**: Edit files in the `app/` directory
2. **Rebuild**: `docker-compose build <service-name>`
3. **Restart**: `docker-compose up -d <service-name>`

### Hot Reload (Development)

For development, you can mount volumes for hot reloading:

```yaml
# In docker-compose.yml, add volumes to services:
volumes:
  - ../app/api-service:/app
```

## 📦 Production Deployment

For production deployment:

1. **Build Images**: `docker-compose build`
2. **Push to Registry**: Tag and push images to your registry
3. **Deploy**: Use Kubernetes manifests in the `manifests/` directory

## 🧪 Testing

### API Testing

```bash
# Test API health
curl http://localhost:8000/healthz

# Test API endpoints
curl http://localhost:8000/api/assets
curl http://localhost:8000/api/events
curl http://localhost:8000/api/stats
```

### Frontend Testing

Open http://localhost:3000 in your browser and navigate through:
- Dashboard
- Assets
- Events
- Stats

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
