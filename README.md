# AssetTrack - Asset Management System

This repository contains the complete AssetTrack application suite for air-gapped Kubernetes environments, maintained by Engineer B. Infrastructure (cluster, Harbor, ArgoCD, Velero, monitoring, logging) is provided separately by Engineer A under `aether/`.

## Architecture Overview

AssetTrack is a microservices-based asset management system with the following components:

### Core Services
- **Agent Service**: DaemonSet that collects asset events from each node
- **Collector Service**: Processes RabbitMQ messages and aggregates events
- **Processor Service**: Core business logic and data persistence
- **API Service**: REST API gateway for external access
- **Web UI**: React-based frontend application

### Data Flow
```
[Node Agents] → [RabbitMQ] → [Collector] → [Processor] → [PostgreSQL]
                                                      ↓
[Web UI] ← [API Service] ← [Processor]
```

## Repository Structure

```
aether-apps/
├── app/                              # Application microservices
│   ├── agent-service/                 # Collects asset events on each node
│   ├── collector-service/             # Consumes RabbitMQ messages from Agents
│   ├── processor-service/             # Processes + stores data into Postgres
│   ├── api-service/                   # FastAPI backend (REST API / gRPC)
│   └── webapp-ui/                     # Frontend web app (React + Nginx)
│
├── infra/                             # Local Dev dependencies
│   ├── docker-compose.yml             # Runs all services + RabbitMQ + Postgres
│   └── env.example                    # Environment variables template
│
├── ci/                                # CI/CD automation
│   ├── Jenkinsfile                    # Jenkins pipeline
│   ├── github-actions.yml             # GitHub Actions workflow
│   └── build_push.sh                  # Script to build + push images to Harbor
│
├── manifests/                         # Kubernetes manifests
│   ├── argocd/                        # ArgoCD Application configuration
│   ├── agent/                         # Agent service DaemonSet
│   ├── collector/                     # Collector service deployment
│   ├── processor/                     # Processor service deployment + HPA
│   ├── api/                           # API service deployment
│   ├── webapp-ui/                     # Web UI deployment
│   ├── ingress.yaml                   # Ingress configuration
│   ├── networkpolicies/               # Network security policies
│   ├── security/                      # RBAC and security policies
│   ├── monitoring/                    # Prometheus rules and Grafana dashboards
│   └── dr/                           # Disaster recovery configurations
│
└── docs/                             # Documentation
    ├── ARCHITECTURE.md               # System architecture overview
    ├── RUNBOOK.md                    # Operational procedures and DR
    └── CONTRIBUTING.md               # Development guidelines
```

## Quick Start

### Local Development
```bash
# Clone and setup
git clone <repository-url>
cd aether-apps

# Setup environment
cp infra/env.example infra/.env
# Edit infra/.env with your configuration

# Start local development stack
cd infra
docker-compose up -d

# Verify services
curl http://localhost:8004/healthz  # API Service
curl http://localhost:3000          # Web UI
```

### Production Deployment

#### 1. Build and Push Images
```bash
# Build all services and push to Harbor
./ci/build_push.sh

# Or build individual services
cd app/processor-service
docker build -t 192.168.0.70/assettrack/processor:v1.0.0 .
docker push 192.168.0.70/assettrack/processor:v1.0.0
```

#### 2. Deploy via ArgoCD
- Commit and push changes in `manifests/` to GitHub
- ArgoCD will auto-sync the `Application` defined in `manifests/argocd/`
- All services are deployed into the `assettrack` namespace

#### 3. Verify Deployment
```bash
kubectl get pods -n assettrack
kubectl get services -n assettrack
kubectl get ingress -n assettrack
```

## Service Endpoints

### Agent Service (DaemonSet)
- `/`: Service status
- `/healthz`: Health check
- `/metrics`: Prometheus metrics
- `/events`: POST endpoint for asset events

### Collector Service
- `/`: Service status
- `/healthz`: Health check
- `/metrics`: Prometheus metrics
- `/stats`: Event statistics
- `/events`: Recent processed events

### Processor Service
- `/`: Service status
- `/healthz`: Health check
- `/metrics`: Prometheus metrics
- `/assets`: Asset CRUD operations

### API Service
- `/`: Service status
- `/healthz`: Health check with downstream status
- `/metrics`: Prometheus metrics
- `/assets`: Asset management API
- `/events`: Event retrieval API
- `/stats`: Statistics API

### Web UI
- `/`: Main application interface
- `/assets`: Asset management page
- `/events`: Event monitoring page
- `/stats`: Statistics dashboard

## Configuration

### Environment Variables
Each service uses ConfigMaps and Secrets for configuration:

**Database Configuration:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`
- `DB_USER`, `DB_PASSWORD` (Secret)

**Message Queue Configuration:**
- `MQ_HOST`, `MQ_PORT`
- `MQ_USER`, `MQ_PASSWORD` (Secret)

**Service URLs:**
- `PROCESSOR_SERVICE_URL`
- `COLLECTOR_SERVICE_URL`

### Security Features
- **Network Policies**: Restrict inter-service communication
- **RBAC**: Role-based access control for all services
- **Pod Security**: Non-root containers, read-only filesystems
- **mTLS**: Service-to-service encryption via Linkerd
- **Ingress Security**: TLS termination and security headers

## Monitoring and Observability

### Metrics
All services expose Prometheus metrics at `/metrics`:
- Service health and availability
- Request rates and response times
- Error rates and business metrics
- Resource utilization

### Logging
- Structured logging across all services
- Centralized collection via Loki
- Log correlation and tracing

### Alerting
- Service down alerts
- High error rate detection
- Performance degradation alerts
- Business metric thresholds

## Disaster Recovery

### Backup Strategy
- Velero scheduled backups
- Database point-in-time recovery
- Configuration backup
- Application state backup

### Recovery Procedures
- Automated restore via Velero
- Manual verification steps
- Data integrity checks
- Service health validation

## Development

### Adding New Services
1. Create service directory in `app/`
2. Add Dockerfile and requirements
3. Create Kubernetes manifests in `manifests/`
4. Update CI/CD pipelines
5. Add monitoring and alerting
6. Update documentation

### Testing
```bash
# Backend tests
cd app/processor-service
python -m pytest

# Frontend tests
cd app/webapp-ui/frontend
npm test

# Integration tests
cd infra
docker-compose -f docker-compose.test.yml up
```

## Documentation
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Operational Runbook](./docs/RUNBOOK.md)
- [Contributing Guidelines](./docs/CONTRIBUTING.md)

## Notes
- Linkerd sidecar injection is enabled via `linkerd.io/inject: enabled` label/annotation
- Ensure Harbor project `assettrack` exists and credentials are configured
- All services run with security best practices (non-root, read-only filesystems)
- Network policies restrict communication to only required paths
