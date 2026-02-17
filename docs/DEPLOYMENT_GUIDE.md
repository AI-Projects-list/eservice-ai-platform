# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Kubernetes 1.24+ (for production)
- kubectl configured to access your cluster
- Helm 3+ (optional, for Helm charts)
- Required API keys (OpenAI, LLM providers, etc.)

## Local Development Deployment

### 1. Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd eservice-ai-platform

# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

### 2. Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, etc.)
docker-compose -f docker/docker-compose.yml up -d

# Verify services
docker-compose -f docker/docker-compose.yml ps

# Check logs
docker-compose -f docker/docker-compose.yml logs -f api
```

### 3. Run Migrations

```bash
# Apply database migrations
make db-migrate

# Or manually
alembic upgrade head
```

### 4. Start API Server

```bash
# Development
make run-dev
# App will be available at http://localhost:8000

# Or production
make run-prod
```

### 5. Access Services

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger**: http://localhost:16686
- **RabbitMQ**: http://localhost:15672 (guest/guest)

## Docker Deployment

### Build Production Image

```bash
# Build Docker image
make docker-build

# Or manually
docker build -f docker/Dockerfile -t eservice-platform:latest .
docker tag eservice-platform:latest eservice-platform:v1.0.0

# Push to registry
docker push eservice-platform:v1.0.0
```

### Run Single Container

```bash
docker run -d \
  --name eservice-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@postgres:5432/eservice" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e OPENAI_API_KEY="sk-..." \
  eservice-platform:latest
```

## Kubernetes Deployment

### 1. Prepare Kubernetes Manifests

```bash
# Create namespace and ConfigMaps
kubectl apply -f k8s/namespace.yaml

# Update secret values in k8s/namespace.yaml before applying
# Edit DATABASE_URL, REDIS_URL, OPENAI_API_KEY, etc.
kubectl apply -f k8s/namespace.yaml
```

### 2. Update Environment-Specific Values

```yaml
# k8s/deployment.yaml
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: eservice-secrets
      key: DATABASE_URL
```

### 3. Deploy Application

```bash
# Deploy all resources
kubectl apply -f k8s/

# Or individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for rollout
kubectl rollout status deployment/eservice-api -n eservice --timeout=5m

# Verify deployment
kubectl get pods -n eservice
kubectl get svc -n eservice
kubectl describe deployment/eservice-api -n eservice
```

### 4. Access Application

```bash
# Get LoadBalancer IP
kubectl get svc eservice-api-service -n eservice

# Access API
curl http://<EXTERNAL-IP>:80/api/v1/health/ping

# Get logs
kubectl logs -f deployment/eservice-api -n eservice

# Interactive debugging
kubectl exec -it <pod-name> -n eservice -- /bin/bash
```

### 5. Scaling

```bash
# Manual scaling
kubectl scale deployment eservice-api --replicas=5 -n eservice

# Autoscaling is configured in HPA (hpa.yaml)
kubectl get hpa -n eservice
kubectl describe hpa eservice-api-hpa -n eservice
```

## Production Deployment

### 1. Pre-deployment Checklist

- [ ] All tests passing (`make test-cov`)
- [ ] Code quality checks passing (`make lint`)
- [ ] Security scan complete (`trivy scan`)
- [ ] Docker image built and pushed to registry
- [ ] Database migrations reviewed
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

### 2. Blue-Green Deployment

```bash
# Create new green deployment
kubectl apply -f k8s/deployment-green.yaml

# Health check green deployment
kubectl get pods -n eservice
kubectl logs deployment/eservice-api-green -n eservice

# Switch traffic (update service selector)
kubectl patch service eservice-api-service -n eservice \
  -p '{"spec":{"selector":{"deployment":"eservice-api-green"}}}'

# Monitor for errors
watch kubectl get pods -n eservice

# If errors, switch back
kubectl patch service eservice-api-service -n eservice \
  -p '{"spec":{"selector":{"deployment":"eservice-api"}}}'

# When stable, delete blue
kubectl delete deployment eservice-api-blue -n eservice
```

### 3. Canary Deployment

```bash
# Deploy canary with reduced replicas
kubectl set image deployment/eservice-api \
  api=eservice-platform:v1.1-canary \
  -n eservice --record

# Monitor metrics
kubectl top pods -n eservice
kubectl describe hpa -n eservice

# Gradual rollout
kubectl set image deployment/eservice-api \
  api=eservice-platform:v1.1 \
  -n eservice --record
```

### 4. Rolling Update (Default)

```bash
# Update image
kubectl set image deployment/eservice-api \
  api=eservice-platform:v1.1 \
  -n eservice --record

# Monitor rollout
kubectl rollout status deployment/eservice-api -n eservice

# If rollout fails, automatic rollback
kubectl rollout undo deployment/eservice-api -n eservice
kubectl rollout status deployment/eservice-api -n eservice
```

## Database Setup

### PostgreSQL Setup

```bash
# Connect to database
psql postgresql://user:password@localhost:5432/eservice

# Run migrations
alembic upgrade head

# Create indexes
CREATE INDEX idx_tickets_customer_status ON tickets(customer_id, status);
CREATE INDEX idx_tickets_created_status ON tickets(created_at, status);
CREATE INDEX idx_kb_published_category ON knowledge_base(published, category);
```

### Database Backup

```bash
# Full backup
pg_dump postgresql://user:password@localhost:5432/eservice \
  > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_20240217.sql

# Upload to S3
aws s3 cp backup_20240217.sql.gz s3://eservice-backups/

# Restore from backup
psql postgresql://user:password@localhost:5432/eservice \
  < backup_20240217.sql
```

## Secrets Management

### Using HashiCorp Vault

```bash
# Store secrets in Vault
vault kv put secret/eservice-prod \
  DATABASE_URL="postgresql://..." \
  OPENAI_API_KEY="sk-..." \
  REDIS_URL="redis://..."

# Reference in K8s
kubectl create secret generic eservice-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  -n eservice
```

### Using Environment Variables

```bash
# Load from .env file
export $(grep -v '^#' .env.prod | xargs)

# Deploy with env vars
kubectl set env deployment/eservice-api \
  DATABASE_URL=$DATABASE_URL \
  OPENAI_API_KEY=$OPENAI_API_KEY \
  -n eservice
```

## Monitoring & Alerting

### Access Monitoring Stack

```bash
# Prometheus
kubectl port-forward -n eservice svc/prometheus 9090:9090
# http://localhost:9090

# Grafana
kubectl port-forward -n eservice svc/grafana 3000:3000
# http://localhost:3000 (admin/admin)

# Jaeger
kubectl port-forward -n eservice svc/jaeger 16686:16686
# http://localhost:16686
```

### Setup Alerts

```yaml
# monitoring/prometheus/rules.yml
groups:
- name: eservice_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    action:
      - send_email to: ops@lenovo.com
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n eservice

# View logs
kubectl logs <pod-name> -n eservice
kubectl logs <pod-name> -n eservice --previous  # Previous restart

# Check resource availability
kubectl get nodes
kubectl top nodes
kubectl top pods -n eservice
```

### Database Connection Issues

```bash
# Test database connection
psql postgresql://user:password@host:5432/eservice

# Check credentials in secrets
kubectl get secret eservice-secrets -n eservice -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Verify database service is running
kubectl get svc -n eservice
```

### LLM Provider Issues

```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check provider configuration
kubectl exec <pod> -n eservice -- \
  python -c "from src.llm.providers import LLMProviderFactory; \
  provider = LLMProviderFactory.get_provider('openai'); print('OK')"
```

## Helm Deployment (Optional)

### Install Helm Chart

```bash
# Create values override
cat > values.yaml <<EOF
image:
  repository: eservice-platform
  tag: v1.0.0
  pullPolicy: Always

replicas: 3

environment: production

secrets:
  DATABASE_URL: "postgresql://..."
  OPENAI_API_KEY: "sk-..."
  REDIS_URL: "redis://..."
EOF

# Install chart
helm install eservice ./k8s/helm-chart -f values.yaml -n eservice

# Upgrade
helm upgrade eservice ./k8s/helm-chart -f values.yaml -n eservice

# Rollback
helm rollback eservice 1 -n eservice
```

## Cleanup

```bash
# Stop Docker Compose
make docker-down

# Delete Kubernetes deployment
kubectl delete -f k8s/ -n eservice
kubectl delete namespace eservice

# Prune unused resources
docker system prune -a --volumes
```
