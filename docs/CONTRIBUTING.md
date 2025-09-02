# Contributing to AssetTrack

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- kubectl (for Kubernetes deployment)
- Access to Harbor registry

### Local Development Environment

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd aether-apps
```

#### 2. Set Up Environment Variables
```bash
cp infra/env.example infra/.env
# Edit infra/.env with your local configuration
```

#### 3. Start Local Development Stack
```bash
cd infra
docker-compose up -d
```

#### 4. Verify Services
```bash
# Check all services are running
docker-compose ps

# Test API endpoints
curl http://localhost:8004/healthz
curl http://localhost:3000
```

### Development Workflow

#### 1. Backend Development
```bash
# Navigate to service directory
cd app/processor-service

# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Development
```bash
# Navigate to frontend directory
cd app/webapp-ui/frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### 3. Testing
```bash
# Run backend tests
cd app/processor-service
python -m pytest

# Run frontend tests
cd app/webapp-ui/frontend
npm test
```

## Code Standards

### Python (Backend Services)
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions
- Maximum line length: 88 characters (Black formatter)
- Use async/await for I/O operations

### JavaScript/React (Frontend)
- Use ESLint and Prettier
- Follow React best practices
- Use functional components with hooks
- Implement proper error boundaries
- Write unit tests for components

### Docker
- Use multi-stage builds
- Minimize image size
- Use non-root users
- Include health checks
- Use specific base image tags

### Kubernetes Manifests
- Use consistent naming conventions
- Include resource limits and requests
- Implement proper security contexts
- Use ConfigMaps and Secrets appropriately
- Include health checks and readiness probes

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates

### Commit Messages
- Use conventional commit format
- Keep commits atomic and focused
- Include issue numbers when applicable

Example:
```
feat(processor): add asset validation endpoint

- Add POST /assets/validate endpoint
- Implement input validation logic
- Add unit tests for validation

Closes #123
```

### Pull Request Process
1. Create feature branch from main
2. Make changes following code standards
3. Write/update tests
4. Update documentation
5. Create pull request with description
6. Request review from team members
7. Address review comments
8. Merge after approval

## Testing Guidelines

### Backend Testing
- Unit tests for all business logic
- Integration tests for API endpoints
- Mock external dependencies
- Test error scenarios
- Maintain >80% code coverage

### Frontend Testing
- Unit tests for components
- Integration tests for user flows
- Mock API calls
- Test responsive design
- Accessibility testing

### End-to-End Testing
- Test complete user workflows
- Verify service integration
- Test deployment scenarios
- Performance testing

## Deployment Process

### Development Deployment
```bash
# Build and push images
./ci/build_push.sh

# Deploy to development cluster
kubectl apply -f manifests/
```

### Production Deployment
1. Create release branch
2. Update version tags
3. Run full test suite
4. Build and push images
5. Deploy via ArgoCD
6. Verify deployment
7. Monitor for issues

## Monitoring and Observability

### Metrics
- Implement Prometheus metrics
- Use consistent naming conventions
- Include business metrics
- Monitor resource usage

### Logging
- Use structured logging
- Include correlation IDs
- Log at appropriate levels
- Avoid sensitive data in logs

### Alerting
- Set up meaningful alerts
- Test alert conditions
- Document alert procedures
- Review and tune thresholds

## Security Guidelines

### Code Security
- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Follow OWASP guidelines
- Regular security audits

### Infrastructure Security
- Use least privilege principle
- Implement network policies
- Secure secrets management
- Regular vulnerability scans
- Keep dependencies updated

## Documentation

### Code Documentation
- Document complex logic
- Include usage examples
- Keep README files updated
- Document API endpoints

### Operational Documentation
- Update runbooks
- Document procedures
- Include troubleshooting guides
- Maintain architecture diagrams

## Release Process

### Version Management
- Use semantic versioning
- Update CHANGELOG.md
- Tag releases in Git
- Create release notes

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Backup procedures verified
- [ ] Rollback plan prepared

## Support and Maintenance

### Bug Reports
- Use issue templates
- Include reproduction steps
- Provide relevant logs
- Specify environment details

### Feature Requests
- Describe use case
- Include acceptance criteria
- Consider implementation effort
- Discuss with team

### Maintenance Tasks
- Regular dependency updates
- Security patches
- Performance optimization
- Code refactoring

## Contact and Resources

### Team Contacts
- **Lead Developer**: [Contact Info]
- **DevOps Engineer**: [Contact Info]
- **QA Engineer**: [Contact Info]

### Useful Links
- [Architecture Documentation](./ARCHITECTURE.md)
- [Runbook](./RUNBOOK.md)
- [API Documentation](./API.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)

