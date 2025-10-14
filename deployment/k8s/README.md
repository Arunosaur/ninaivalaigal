# Kubernetes & GitOps Deployment

This directory contains Kubernetes manifests and GitOps configuration for deploying Ninaivalaigal using ArgoCD.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │     Staging     │    │   Production    │
│   Environment   │    │   Environment   │    │   Environment   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 1 replica     │    │ • 2 replicas    │    │ • 3 replicas    │
│ • Debug enabled │    │ • Perf testing  │    │ • High availability│
│ • Local storage │    │ • Staging data  │    │ • Prod data     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   ArgoCD GitOps │
                    │   Orchestration │
                    ├─────────────────┤
                    │ • Auto Sync     │
                    │ • Health Checks │
                    │ • Rollbacks     │
                    │ • Notifications │
                    └─────────────────┘
```

## 📁 Directory Structure

```
k8s/
├── base/                           # Base Kubernetes manifests
│   ├── api-server/                 # API server deployment
│   ├── postgresql/                 # PostgreSQL database
│   ├── redis/                      # Redis cache
│   └── ingress/                    # Ingress configuration
├── overlays/                       # Environment-specific overlays
│   ├── dev/                        # Development environment
│   ├── staging/                    # Staging environment
│   └── prod/                       # Production environment
└── argocd/                         # ArgoCD GitOps configuration
    ├── applications/               # ArgoCD applications
    └── projects/                   # ArgoCD projects
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (local or cloud)
- kubectl configured
- Docker registry access
- ArgoCD installed

### 1. Setup ArgoCD

```bash
# Run the setup script
./scripts/setup-argocd.sh
```

### 2. Deploy to Development

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/dev/
```

### 3. Access the Application

```bash
# Port-forward to access locally
kubectl port-forward svc/ninaivalaigal-api-service 8080:80 -n ninaivalaigal-dev
```

## 🔧 Configuration

### Environment Variables

Each environment uses different configurations:

- **Development**: Debug enabled, single replica, local storage
- **Staging**: Performance testing, 2 replicas, staging data
- **Production**: High availability, 3 replicas, production data

### Secrets Management

Secrets are managed through Kubernetes secrets:

```bash
# Create database secret
kubectl create secret generic database-secret \
  --from-literal=url="postgresql://user:pass@host:5432/db" \
  -n ninaivalaigal-dev
```

### Resource Limits

| Environment | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------------|-------------|-----------|----------------|--------------|
| Development | 100m        | 200m      | 128Mi          | 256Mi        |
| Staging     | 250m        | 500m      | 256Mi          | 512Mi        |
| Production  | 500m        | 1000m     | 512Mi          | 1Gi          |

## 📊 Monitoring & Health Checks

### Health Endpoints

- **Liveness**: `/health` - Application health
- **Readiness**: `/ready` - Ready to serve traffic
- **Metrics**: `/metrics` - Prometheus metrics

### ArgoCD Monitoring

ArgoCD provides:
- Application sync status
- Health status monitoring
- Deployment history
- Rollback capabilities

## 🔄 GitOps Workflow

### Deployment Process

1. **Code Push**: Developer pushes code to main branch
2. **CI Build**: GitHub Actions builds and pushes container image
3. **GitOps Update**: Image tags updated in kustomization files
4. **ArgoCD Sync**: ArgoCD detects changes and syncs to cluster
5. **Health Check**: ArgoCD monitors deployment health

### Promotion Pipeline

```
main branch → dev environment → staging environment → prod environment
     ↓              ↓                    ↓                    ↓
  Auto deploy   Auto deploy        Manual approval     Manual approval
```

## 🛡️ Security

### Network Policies

Network policies restrict traffic between pods:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-netpol
spec:
  podSelector:
    matchLabels:
      app: ninaivalaigal-api
  policyTypes:
  - Ingress
  - Egress
```

### RBAC

Role-based access control for ArgoCD:

- **Developers**: Read/sync access to dev environment
- **Operators**: Full access to all environments
- **Viewers**: Read-only access

## 📈 Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ninaivalaigal-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ninaivalaigal-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔍 Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   kubectl describe pod <pod-name> -n ninaivalaigal-dev
   ```

2. **ArgoCD Sync Issues**
   ```bash
   argocd app get ninaivalaigal-dev
   argocd app sync ninaivalaigal-dev --force
   ```

3. **Database Connection Issues**
   ```bash
   kubectl logs deployment/ninaivalaigal-api -n ninaivalaigal-dev
   ```

### Useful Commands

```bash
# Check application status
kubectl get all -n ninaivalaigal-dev

# View logs
kubectl logs -f deployment/ninaivalaigal-api -n ninaivalaigal-dev

# Execute into pod
kubectl exec -it deployment/ninaivalaigal-api -n ninaivalaigal-dev -- /bin/bash

# Port forward for debugging
kubectl port-forward svc/postgresql-service 5432:5432 -n ninaivalaigal-dev
```

## 🎯 Performance Targets

- **Deployment Time**: <5 minutes
- **Rollback Time**: <2 minutes
- **Application Startup**: <30 seconds
- **Health Check Response**: <5 seconds
- **Resource Utilization**: >80% efficiency

## 🚀 Next Steps

1. **SPEC-022**: ArgoCD Advanced Configuration
2. **SPEC-023**: Multi-Environment Promotion Pipeline
3. **SPEC-024**: Horizontal Autoscaling & Resource Management

Built on the bulletproof Phase 2B foundation! 🎊
