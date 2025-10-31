---
title: Untitled SPEC
---


# SPEC-021: GitOps with ArgoCD + Kubernetes Deployment

**Status**: 🚧 In Progress
**Priority**: High
**Phase**: 3A - Operational Maturity
**Dependencies**: Phase 2B Bulletproof Foundation

## 🎯 Objective

Implement production-grade GitOps deployment using ArgoCD and Kubernetes, transitioning from course/demo level to enterprise-grade deployment infrastructure.

## 📋 Requirements

### Core Requirements
- **R1**: Kubernetes manifests for all services (API, PostgreSQL, Redis)
- **R2**: Helm charts for templated deployments
- **R3**: ArgoCD GitOps pipeline for automated deployment
- **R4**: Multi-environment support (dev/staging/prod)
- **R5**: Container registry integration
- **R6**: Service mesh configuration (Istio)
- **R7**: Ingress and load balancing
- **R8**: Persistent volume management

### Performance Requirements
- **P1**: Deployment time &lt;5 minutes
- **P2**: Rollback time &lt;2 minutes
- **P3**: Zero-downtime deployments
- **P4**: Health check response &lt;30 seconds

## 🏗️ Architecture

### GitOps Flow
```
Developer → Git Push → ArgoCD → Kubernetes → Production
     ↓           ↓         ↓          ↓
   Local    GitHub    Sync &     Deploy &
   Dev      Repo      Monitor    Monitor
```

### Kubernetes Stack
- **Namespace**: `ninaivalaigal-{env}`
- **Services**: API Server, PostgreSQL, Redis, Monitoring
- **Ingress**: NGINX Ingress Controller
- **Storage**: Persistent Volumes for databases
- **Monitoring**: Prometheus + Grafana

## 📁 Folder Structure

```
k8s/
├── base/                           # Kustomize base configurations
│   ├── api-server/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── postgresql/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── secret.yaml
│   ├── redis/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── ingress/
│       └── ingress.yaml
├── overlays/                       # Environment-specific overlays
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── prod/
│       ├── kustomization.yaml
│       └── patches/
├── helm/                           # Helm charts
│   └── ninaivalaigal/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-dev.yaml
│       ├── values-staging.yaml
│       ├── values-prod.yaml
│       └── templates/
└── argocd/                         # ArgoCD applications
    ├── applications/
    │   ├── ninaivalaigal-dev.yaml
    │   ├── ninaivalaigal-staging.yaml
    │   └── ninaivalaigal-prod.yaml
    └── projects/
        └── ninaivalaigal.yaml
```

## 🚀 Implementation Plan

### Phase 1: Base Kubernetes Manifests (Week 1)
1. Create base deployments for all services
2. Configure services and networking
3. Set up persistent storage
4. Implement health checks

### Phase 2: ArgoCD GitOps (Week 2)
1. Install ArgoCD in cluster
2. Configure GitOps applications
3. Set up automated sync policies
4. Implement rollback strategies

### Phase 3: Multi-Environment (Week 3)
1. Create environment overlays
2. Configure promotion pipelines
3. Set up environment-specific secrets
4. Implement environment health monitoring

## 📊 Success Metrics

- **Deployment Speed**: &lt;5 minutes end-to-end
- **Rollback Speed**: &lt;2 minutes to previous version
- **Uptime**: 99.9% availability during deployments
- **Environment Parity**: 100% configuration consistency
- **GitOps Sync**: &lt;30 seconds from git push to deployment

## 🔄 Next Steps

1. **Immediate**: Create base Kubernetes manifests
2. **Week 1**: Set up ArgoCD and GitOps pipeline
3. **Week 2**: Configure multi-environment deployment
4. **Week 3**: Integrate with existing CI/CD from Phase 2B

Ready to implement immediately on the bulletproof Phase 2B foundation! 🚀

---

## Related Documentation

### Implementation Files
- **ArgoCD Setup:** `/argocd/` - ArgoCD configuration and installation
- **K8s Manifests:** `/deployment/k8s/` - Kubernetes deployments and overlays
- **Scripts:** `/scripts/argocd-*.sh` - Automation scripts

### Architecture Documents
- [Kubernetes Deployment Guide](/deployment/k8s/README.md)
- [ArgoCD Operations Manual](/argocd/README.md)
- [Testing Results](/docs/ARGOCD_TESTING_RESULTS.md)

### Related SPECs
- **SPEC-015:** Kubernetes Deployment Strategy
- **SPEC-016:** CI/CD Pipeline Architecture
- **SPEC-022:** Kubernetes Monitoring with Prometheus + Grafana

### Taiga Tasks
- **US#149:** SPEC-021 Implementation & Validation
- **Task #150:** Performance Validation (deployment time, rollback time)
- **Task #151:** Functional Validation (auto-sync, RBAC, multi-env)

---

## Implementation Status

✅ **Phase 1: Base Kubernetes Manifests** - COMPLETE
- Base deployments created for all services
- Persistent storage configured
- Health checks implemented

✅ **Phase 2: ArgoCD GitOps Setup** - COMPLETE
- ArgoCD installed and configured
- GitOps applications defined
- Automated sync policies implemented
- Rollback strategies defined

✅ **Phase 3: Multi-Environment Configuration** - COMPLETE
- Environment overlays created (dev/staging/prod)
- Kustomization setup complete
- Environment-specific configurations

🟡 **Phase 4: Production Validation** - IN PROGRESS
- Performance validation needed
- Functional requirements verification
- See Taiga US#149 for validation tasks

---

**Last Updated:** October 30, 2025 (Taiga cross-references added)
**Status:** Implemented ✅ - Validation pending
