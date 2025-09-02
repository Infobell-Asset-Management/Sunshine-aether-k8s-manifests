# AssetTrack Runbook

## Emergency Procedures

### Service Outage Response

#### 1. Service Health Check
```bash
# Check all services in the namespace
kubectl get pods -n assettrack

# Check service endpoints
kubectl get endpoints -n assettrack

# Check service logs
kubectl logs -n assettrack deployment/processor-service
kubectl logs -n assettrack deployment/collector-service
kubectl logs -n assettrack deployment/api-service
```

#### 2. Database Connectivity Issues
```bash
# Check database connectivity
kubectl exec -n assettrack deployment/processor-service -- curl -f http://localhost:8000/healthz

# Check database logs (if accessible)
kubectl logs -n postgres deployment/postgres
```

#### 3. Message Queue Issues
```bash
# Check RabbitMQ connectivity
kubectl exec -n assettrack deployment/collector-service -- curl -f http://localhost:8000/healthz

# Check RabbitMQ management interface
kubectl port-forward -n rabbitmq svc/rabbitmq 15672:15672
```

### Disaster Recovery Procedures

#### 1. Backup Verification
```bash
# List available backups
velero backup get

# Check backup details
velero backup describe <backup-name>

# Verify backup contents
velero backup logs <backup-name>
```

#### 2. Full System Restore
```bash
# Create restore from latest backup
velero restore create --from-backup <backup-name> --include-namespaces assettrack

# Monitor restore progress
velero restore get
velero restore describe <restore-name>

# Verify restore completion
kubectl get pods -n assettrack
kubectl get services -n assettrack
```

#### 3. Partial Restore (Specific Services)
```bash
# Restore specific service
velero restore create --from-backup <backup-name> \
  --include-namespaces assettrack \
  --include-resources deployments \
  --selector app=processor-service
```

### Performance Troubleshooting

#### 1. High Response Times
```bash
# Check service metrics
kubectl exec -n assettrack deployment/api-service -- curl http://localhost:8000/metrics

# Check resource usage
kubectl top pods -n assettrack

# Check HPA status
kubectl get hpa -n assettrack
```

#### 2. Memory Issues
```bash
# Check memory usage
kubectl top pods -n assettrack --sort-by=memory

# Check for OOM kills
kubectl describe pods -n assettrack | grep -i "oom"

# Check container logs for memory errors
kubectl logs -n assettrack deployment/processor-service | grep -i "memory"
```

#### 3. Database Performance
```bash
# Check database connections
kubectl exec -n assettrack deployment/processor-service -- curl http://localhost:8000/healthz

# Check slow queries (if accessible)
kubectl exec -n postgres deployment/postgres -- psql -c "SELECT * FROM pg_stat_activity;"
```

### Security Incidents

#### 1. Unauthorized Access
```bash
# Check for suspicious pods
kubectl get pods -n assettrack -o wide

# Check network policies
kubectl get networkpolicies -n assettrack

# Check RBAC
kubectl get rolebindings -n assettrack
kubectl get serviceaccounts -n assettrack
```

#### 2. Data Breach Response
```bash
# Isolate affected services
kubectl scale deployment processor-service --replicas=0 -n assettrack

# Check audit logs
kubectl get events -n assettrack --sort-by='.lastTimestamp'

# Review network traffic
kubectl logs -n assettrack deployment/api-service | grep -i "unauthorized"
```

## Maintenance Procedures

### Rolling Updates

#### 1. Application Update
```bash
# Update image tag in deployment
kubectl set image deployment/processor-service processor-service=192.168.0.70/assettrack/processor-service:v1.1.0 -n assettrack

# Monitor rollout
kubectl rollout status deployment/processor-service -n assettrack

# Rollback if needed
kubectl rollout undo deployment/processor-service -n assettrack
```

#### 2. Configuration Update
```bash
# Update ConfigMap
kubectl apply -f manifests/processor/configmap.yaml

# Restart pods to pick up new config
kubectl rollout restart deployment/processor-service -n assettrack
```

### Backup Procedures

#### 1. Manual Backup
```bash
# Create manual backup
velero backup create assettrack-manual-$(date +%Y%m%d-%H%M%S) \
  --include-namespaces assettrack \
  --include-resources deployments,services,configmaps,secrets

# Verify backup
velero backup describe assettrack-manual-$(date +%Y%m%d-%H%M%S)
```

#### 2. Database Backup
```bash
# Create database dump
kubectl exec -n postgres deployment/postgres -- pg_dump -U assettrack assettrack > backup-$(date +%Y%m%d).sql

# Verify backup file
ls -la backup-$(date +%Y%m%d).sql
```

### Monitoring and Alerting

#### 1. Check Alert Status
```bash
# Check Prometheus alerts
kubectl port-forward -n monitoring svc/prometheus-k8s 9090:9090

# Check Alertmanager
kubectl port-forward -n monitoring svc/alertmanager-main 9093:9093
```

#### 2. Update Alert Rules
```bash
# Apply new alert rules
kubectl apply -f manifests/monitoring/prometheus-rules.yaml

# Verify rules are loaded
kubectl get prometheusrules -n assettrack
```

## Troubleshooting Commands

### General Debugging
```bash
# Get detailed pod information
kubectl describe pod <pod-name> -n assettrack

# Check events
kubectl get events -n assettrack --sort-by='.lastTimestamp'

# Check service endpoints
kubectl get endpoints -n assettrack

# Check ingress status
kubectl get ingress -n assettrack
kubectl describe ingress assettrack-ingress -n assettrack
```

### Network Debugging
```bash
# Test service connectivity
kubectl run test-pod --image=busybox -n assettrack --rm -it --restart=Never -- sh

# From test pod, test connectivity
wget -qO- http://processor-service:8000/healthz
wget -qO- http://collector-service:8000/healthz
wget -qO- http://api-service:8000/healthz
```

### Log Analysis
```bash
# Follow logs in real-time
kubectl logs -f deployment/processor-service -n assettrack

# Search logs for errors
kubectl logs deployment/api-service -n assettrack | grep -i error

# Get logs from specific time
kubectl logs deployment/collector-service -n assettrack --since=1h
```

## Contact Information

### Emergency Contacts
- **Engineer A (Infrastructure)**: [Contact Info]
- **Engineer B (Application)**: [Contact Info]
- **On-Call**: [Contact Info]

### Escalation Matrix
1. **Level 1**: Application team (Engineer B)
2. **Level 2**: Infrastructure team (Engineer A)
3. **Level 3**: Management escalation

### Documentation Links
- [Architecture Documentation](./ARCHITECTURE.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Velero Documentation](https://velero.io/docs/)

