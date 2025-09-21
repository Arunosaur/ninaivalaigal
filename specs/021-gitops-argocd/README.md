# SPEC-021: GitOps Deployment via ArgoCD

## Title
GitOps-Based Continuous Delivery with ArgoCD

## Objective
Enable declarative, version-controlled Kubernetes deployments using ArgoCD.

## Features

- Deploy `argocd` into `argocd/` namespace
- `Application.yaml` pointing to `ninaivalaigal/k8s/`
- Auto-sync on PR merge or tag release
- Rollback and deployment history

## Implementation Targets

- Helm or Kustomize support
- GitHub webhook or polling sync
- Read-only UI access for audit

## Technical Requirements

### ArgoCD Installation
```yaml
# argocd/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
```

### Application Configuration
```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ninaivalaigal
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Arunosaur/ninaivalaigal
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: ninaivalaigal
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Success Criteria
- [ ] ArgoCD deployed and accessible
- [ ] Application syncs automatically on git push
- [ ] Rollback functionality working
- [ ] UI provides deployment history

## Status
📋 Planned
