# SPEC-015: Kubernetes Deployment Strategy

## Overview

This specification defines the Kubernetes deployment strategy for ninaivalaigal, providing enterprise-grade container orchestration with proper resource management, scaling, security, and observability across any Kubernetes cluster.

## Motivation

- **Enterprise Orchestration**: Professional container management with Kubernetes
- **Universal Deployment**: Works on any Kubernetes cluster (EKS, GKE, AKS, on-premises)
- **Auto-scaling**: Horizontal Pod Autoscaling based on resource utilization
- **High Availability**: Multi-replica deployments with proper health checks
- **Security**: RBAC, network policies, and secret management
- **Observability**: Integration with Kubernetes-native monitoring

## Specification

### 1. Kubernetes Architecture

#### 1.1 Namespace Strategy
```yaml
Namespace: ninaivalaigal
Purpose: Isolation and resource management
Labels:
  app: ninaivalaigal
  version: v1.0.0
```

#### 1.2 Component Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   Service       │    │   Deployment    │
│   (External)    │───▶│   (Internal)    │───▶│   (Pods)        │
│   Load Balancer │    │   Load Balancer │    │   ninaivalaigal │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌─────────────────┐
                                               │   ConfigMap     │
                                               │   Secrets       │
                                               │   PVC           │
                                               └─────────────────┘
```

### 2. Kubernetes Manifests

#### 2.1 Namespace Configuration
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ninaivalaigal
  labels:
    app: ninaivalaigal
    version: v1.0.0
```

#### 2.2 PostgreSQL Database
```yaml
# k8s/postgres.yaml
Components:
  - ConfigMap: postgres-config (environment variables)
  - Secret: postgres-secret (passwords)
  - PersistentVolumeClaim: postgres-pvc (data storage)
  - Deployment: postgres (database server)
  - Service: postgres (internal networking)

Image: ghcr.io/arunosaur/ninaivalaigal-postgres:latest
Storage: 10Gi persistent volume
Health Checks: pg_isready probes
```

#### 2.3 API Application
```yaml
# k8s/api.yaml
Components:
  - ConfigMap: api-config (environment variables)
  - Secret: api-secret (JWT secrets)
  - Deployment: ninaivalaigal-api (application)
  - Service: ninaivalaigal-api (internal networking)
  - Ingress: ninaivalaigal-ingress (external access)

Image: ghcr.io/arunosaur/ninaivalaigal-api:latest
Replicas: 3 (high availability)
Resources: 256Mi memory, 250m CPU (requests)
Health Checks: /health endpoint probes
```

### 3. Container Registry Integration

#### 3.1 GHCR Authentication
```yaml
# k8s/ghcr-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ghcr-pull-secret
  namespace: ninaivalaigal
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <BASE64_ENCODED_DOCKER_CONFIG>
```

#### 3.2 Image Pull Configuration
```yaml
# In deployment spec
spec:
  template:
    spec:
      imagePullSecrets:
      - name: ghcr-pull-secret
      containers:
      - name: api
        image: ghcr.io/arunosaur/ninaivalaigal-api:latest
        imagePullPolicy: Always
```

### 4. Resource Management

#### 4.1 Resource Requests and Limits
```yaml
# API Container Resources
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# PostgreSQL Container Resources
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### 4.2 Horizontal Pod Autoscaling
```yaml
# Future enhancement
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

### 5. Health Checks and Probes

#### 5.1 Liveness Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

#### 5.2 Readiness Probes
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

#### 5.3 Startup Probes
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30
```

### 6. Networking and Ingress

#### 6.1 Service Configuration
```yaml
# Internal service for API
apiVersion: v1
kind: Service
metadata:
  name: ninaivalaigal-api
  namespace: ninaivalaigal
spec:
  selector:
    app: ninaivalaigal-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### 6.2 Ingress Configuration
```yaml
# External access via Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ninaivalaigal-ingress
  namespace: ninaivalaigal
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.ninaivalaigal.com
    secretName: ninaivalaigal-tls
  rules:
  - host: api.ninaivalaigal.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ninaivalaigal-api
            port:
              number: 8000
```

### 7. Configuration Management

#### 7.1 ConfigMaps
```yaml
# Non-sensitive configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: ninaivalaigal
data:
  DATABASE_URL: postgresql://nina:change_me_securely@postgres:5432/nina
  NINAIVALAIGAL_DATABASE_URL: postgresql://nina:change_me_securely@postgres:5432/nina
  MEMORY_PROVIDER: native
```

#### 7.2 Secrets
```yaml
# Sensitive configuration
apiVersion: v1
kind: Secret
metadata:
  name: api-secret
  namespace: ninaivalaigal
type: Opaque
data:
  NINAIVALAIGAL_JWT_SECRET: <BASE64_ENCODED_JWT_SECRET>
```

### 8. Kustomization

#### 8.1 Kustomization Configuration
```yaml
# k8s/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ninaivalaigal

resources:
  - namespace.yaml
  - postgres.yaml
  - api.yaml

commonLabels:
  app: ninaivalaigal
  version: v1.0.0

images:
  - name: ghcr.io/arunosaur/ninaivalaigal-postgres
    newTag: latest
  - name: ghcr.io/arunosaur/ninaivalaigal-api
    newTag: latest
```

## Implementation

### 1. Makefile Integration
```makefile
# Kubernetes deployment commands
k8s-deploy:     # Deploy to Kubernetes
k8s-status:     # Check deployment status
k8s-logs:       # View application logs
k8s-delete:     # Delete deployment
```

### 2. Deployment Commands
```bash
# Deploy complete stack
kubectl apply -k k8s/

# Check deployment status
kubectl get all -n ninaivalaigal

# View logs
kubectl logs -n ninaivalaigal -l app=ninaivalaigal-api --tail=50

# Delete deployment
kubectl delete -k k8s/
```

### 3. GHCR Secret Creation
```bash
# Create registry secret for private images
kubectl create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username=Arunosaur \
  --docker-password=$GHCR_PAT \
  --docker-email=you@example.com \
  --namespace=ninaivalaigal
```

## Security Considerations

### 1. RBAC (Role-Based Access Control)
```yaml
# Future enhancement: Service accounts and roles
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ninaivalaigal-api
  namespace: ninaivalaigal
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ninaivalaigal-api-role
  namespace: ninaivalaigal
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

### 2. Network Policies
```yaml
# Future enhancement: Network segmentation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ninaivalaigal-network-policy
  namespace: ninaivalaigal
spec:
  podSelector:
    matchLabels:
      app: ninaivalaigal-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
```

### 3. Pod Security Standards
```yaml
# Pod security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

## Monitoring & Observability

### 1. Kubernetes Native Monitoring
```yaml
# ServiceMonitor for Prometheus (if using Prometheus Operator)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ninaivalaigal-api
  namespace: ninaivalaigal
spec:
  selector:
    matchLabels:
      app: ninaivalaigal-api
  endpoints:
  - port: http
    path: /metrics
```

### 2. Health Check Endpoints
- **Liveness**: `/health` - Basic application health
- **Readiness**: `/health` - Ready to serve traffic
- **Metrics**: `/metrics` - Prometheus metrics (if enabled)

### 3. Logging Strategy
```yaml
# Structured logging to stdout/stderr
# Collected by Kubernetes logging system
# Aggregated by cluster logging solution (ELK, Fluentd, etc.)
```

## Testing Strategy

### 1. Local Testing (Kind/Minikube)
```bash
# Create local cluster
kind create cluster --name ninaivalaigal

# Deploy to local cluster
kubectl apply -k k8s/

# Port forward for testing
kubectl port-forward -n ninaivalaigal svc/ninaivalaigal-api 8000:8000

# Test application
curl http://localhost:8000/health
```

### 2. Staging Environment
```bash
# Deploy to staging cluster
kubectl config use-context staging-cluster
kubectl apply -k k8s/

# Run integration tests
kubectl exec -n ninaivalaigal deployment/ninaivalaigal-api -- python -m pytest
```

### 3. Production Validation
```bash
# Deploy to production cluster
kubectl config use-context production-cluster
kubectl apply -k k8s/

# Validate deployment
kubectl get pods -n ninaivalaigal
kubectl logs -n ninaivalaigal -l app=ninaivalaigal-api
```

## Success Criteria

### 1. Functional Requirements
- ✅ All pods start successfully and pass health checks
- ✅ Application is accessible via Ingress
- ✅ Database connectivity works properly
- ✅ Auto-scaling responds to load (future)

### 2. Operational Requirements
- ✅ Deployment is idempotent and repeatable
- ✅ Rolling updates work without downtime
- ✅ Resource limits prevent resource exhaustion
- ✅ Monitoring and logging work properly

### 3. Security Requirements
- ✅ Containers run as non-root users
- ✅ Secrets are properly managed
- ✅ Network access is appropriately restricted
- ✅ RBAC is properly configured (future)

## Future Enhancements

1. **Horizontal Pod Autoscaling**: Implement CPU/memory-based scaling
2. **Vertical Pod Autoscaling**: Automatic resource recommendation
3. **Network Policies**: Implement micro-segmentation
4. **Service Mesh**: Istio integration for advanced traffic management
5. **GitOps**: ArgoCD integration for declarative deployments
6. **Backup Strategy**: Automated database backups with Velero

## Dependencies

- Kubernetes cluster (>= 1.20)
- kubectl CLI tool
- Container registry access (GHCR)
- Ingress controller (nginx, traefik, etc.)
- Persistent volume provisioner
- DNS configuration for custom domains

This specification ensures ninaivalaigal has enterprise-grade Kubernetes deployment capabilities suitable for production workloads across any Kubernetes environment.
