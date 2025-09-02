# AssetTrack Architecture

## Overview

AssetTrack is a microservices-based asset management system designed for air-gapped Kubernetes environments. The system consists of multiple services that work together to collect, process, store, and present asset data.

## Architecture Components

### 1. Agent Service (DaemonSet)
- **Purpose**: Collects asset events from each Kubernetes node
- **Deployment**: Runs as a DaemonSet on all nodes
- **Communication**: Publishes events to RabbitMQ
- **Key Features**:
  - Node-specific asset monitoring
  - Event collection and queuing
  - Health monitoring and metrics

### 2. Collector Service
- **Purpose**: Consumes messages from RabbitMQ and processes events
- **Deployment**: Replicated deployment (2+ replicas)
- **Communication**: Consumes from RabbitMQ, communicates with Processor
- **Key Features**:
  - Event processing and aggregation
  - Message queue management
  - Event statistics and metrics

### 3. Processor Service
- **Purpose**: Core business logic for asset data processing and storage
- **Deployment**: Replicated deployment with HPA
- **Communication**: Interacts with PostgreSQL database
- **Key Features**:
  - Asset CRUD operations
  - Data persistence
  - Business logic processing

### 4. API Service
- **Purpose**: REST API gateway for external access
- **Deployment**: Replicated deployment
- **Communication**: Aggregates data from Processor and Collector
- **Key Features**:
  - REST API endpoints
  - Service aggregation
  - CORS support

### 5. Web UI
- **Purpose**: React-based frontend application
- **Deployment**: Replicated deployment with Nginx
- **Communication**: Consumes API Service
- **Key Features**:
  - Asset management interface
  - Real-time dashboards
  - Event monitoring

## Data Flow

```
[Node Agents] → [RabbitMQ] → [Collector] → [Processor] → [PostgreSQL]
                                                      ↓
[Web UI] ← [API Service] ← [Processor]
```

## Infrastructure Dependencies

### External Services (Provided by Engineer A)
- **PostgreSQL**: Primary database
- **RabbitMQ**: Message queue
- **Harbor**: Container registry
- **ArgoCD**: GitOps deployment
- **Linkerd**: Service mesh
- **Prometheus**: Metrics collection
- **Loki**: Log aggregation
- **Velero**: Backup and DR

### Security Features
- **Network Policies**: Restrict inter-service communication
- **RBAC**: Role-based access control
- **Pod Security**: Non-root containers, read-only filesystems
- **mTLS**: Service-to-service encryption via Linkerd

## Deployment Strategy

### Local Development
- Docker Compose for full stack
- Local PostgreSQL and RabbitMQ
- Hot reloading for development

### Production Deployment
- Kubernetes manifests
- ArgoCD GitOps automation
- Harbor registry integration
- Velero backup scheduling

## Monitoring and Observability

### Metrics
- Service health and availability
- Request rates and response times
- Error rates and business metrics
- Resource utilization

### Logging
- Structured logging across all services
- Centralized log collection via Loki
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

## Scaling Considerations

### Horizontal Scaling
- Stateless service replication
- Database connection pooling
- Message queue partitioning
- Load balancer configuration

### Vertical Scaling
- Resource limits and requests
- HPA configuration
- Database optimization
- Cache implementation

## Security Considerations

### Network Security
- Network policies for service isolation
- Ingress/egress traffic control
- Service mesh security
- TLS termination

### Application Security
- Input validation and sanitization
- Authentication and authorization
- Secret management
- Vulnerability scanning

### Infrastructure Security
- Pod security policies
- RBAC implementation
- Audit logging
- Compliance monitoring

