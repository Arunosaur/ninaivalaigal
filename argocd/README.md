# ArgoCD GitOps Deployment

This directory contains ArgoCD configuration for GitOps-based deployment of ninaivalaigal.

## 🎯 Overview

ArgoCD provides declarative, GitOps continuous delivery for Kubernetes. It automatically syncs your Kubernetes cluster with the desired state defined in Git.

## 📁 Directory Structure

```
argocd/
├── README.md              # This file
├── namespace.yaml          # ArgoCD namespace
├── install.yaml           # ArgoCD installation config
├── application.yaml        # Ninaivalaigal application definition
├── kustomization.yaml      # Kustomize configuration
└── credentials.txt         # Generated credentials (git-ignored)
```

## 🚀 Quick Start

### 1. Install ArgoCD

```bash
# Install ArgoCD and configure ninaivalaigal application
make argocd-install
```

This will:
- Create the `argocd` namespace
- Install ArgoCD v2.9.3
- Create the ninaivalaigal application
- Start port-forwarding to access the UI
- Save credentials to `argocd/credentials.txt`

### 2. Access ArgoCD UI

```bash
# Check status and get access info
make argocd-status

# Open UI (starts port-forward if needed)
make argocd-ui
```

Access the UI at: https://localhost:8080
- Username: `admin`
- Password: See `argocd/credentials.txt`

### 3. Monitor Deployments

```bash
# Check application sync status
make argocd-status

# Manually trigger sync
make argocd-sync
```

## 🔧 Configuration Details

### Application Configuration

The ninaivalaigal application is configured to:

- **Source**: `https://github.com/Arunosaur/ninaivalaigal`
- **Path**: `k8s/` directory
- **Target**: `ninaivalaigal` namespace
- **Sync Policy**: Automated with self-heal and prune
- **Revision**: `HEAD` (latest)

### Auto-Sync Features

- **Prune**: Remove resources not defined in Git
- **Self-Heal**: Automatically fix drift from desired state
- **Create Namespace**: Automatically create target namespace
- **Retry Logic**: 5 retries with exponential backoff

### Project Configuration

The `ninaivalaigal-project` AppProject provides:

- **Source Control**: Restricted to ninaivalaigal repository
- **Destination Control**: Limited to ninaivalaigal namespaces
- **Resource Whitelist**: Only allowed Kubernetes resources
- **RBAC**: Read-only and admin roles

## 🛠️ Management Commands

### Installation & Setup
```bash
make argocd-install      # Install ArgoCD
make argocd-status       # Check status
make argocd-ui          # Access UI
```

### Application Management
```bash
make argocd-sync        # Manual sync
kubectl get applications -n argocd                    # List applications
kubectl describe application ninaivalaigal -n argocd  # Application details
```

### Troubleshooting
```bash
# View ArgoCD server logs
kubectl logs -n argocd deployment/argocd-server

# Restart ArgoCD server
kubectl rollout restart deployment/argocd-server -n argocd

# Check application events
kubectl describe application ninaivalaigal -n argocd
```

### Cleanup
```bash
make argocd-uninstall   # Complete removal
```

## 🔄 GitOps Workflow

### 1. Development Workflow

1. **Make Changes**: Modify Kubernetes manifests in `k8s/` directory
2. **Commit & Push**: Push changes to the repository
3. **Auto-Sync**: ArgoCD detects changes and syncs automatically
4. **Monitor**: Check sync status in ArgoCD UI

### 2. Rollback Process

1. **UI Rollback**: Use ArgoCD UI to rollback to previous revision
2. **CLI Rollback**:
   ```bash
   # Get revision history
   kubectl get application ninaivalaigal -n argocd -o yaml

   # Rollback to specific revision
   kubectl patch application ninaivalaigal -n argocd --type merge -p '{"spec":{"source":{"targetRevision":"<commit-hash>"}}}'
   ```

### 3. Manual Sync

```bash
# Force sync (ignores sync windows)
kubectl patch application ninaivalaigal -n argocd --type merge -p '{"operation":{"sync":{"syncStrategy":{"force":true}}}}'
```

## 🔐 Security Features

### RBAC Configuration

- **Read-Only Role**: View applications and sync status
- **Admin Role**: Full application management
- **Project Isolation**: Resources scoped to ninaivalaigal project

### Resource Restrictions

- **Namespace Limits**: Only ninaivalaigal namespaces
- **Resource Whitelist**: Approved Kubernetes resources only
- **Source Control**: Single repository access

## 📊 Monitoring & Observability

### Health Checks

ArgoCD monitors:
- **Sync Status**: Git vs cluster state
- **Health Status**: Resource health in cluster
- **Operation Status**: Ongoing sync operations

### Metrics Integration

ArgoCD provides Prometheus metrics for:
- Application sync frequency
- Sync success/failure rates
- Resource drift detection
- Performance metrics

## 🚨 Troubleshooting

### Common Issues

1. **Sync Failures**
   ```bash
   # Check application status
   kubectl describe application ninaivalaigal -n argocd

   # View sync operation details
   kubectl get application ninaivalaigal -n argocd -o yaml
   ```

2. **Permission Issues**
   ```bash
   # Check ArgoCD server permissions
   kubectl auth can-i create deployments --as=system:serviceaccount:argocd:argocd-application-controller
   ```

3. **Resource Conflicts**
   ```bash
   # Force refresh application
   kubectl patch application ninaivalaigal -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
   ```

### Debug Commands

```bash
# ArgoCD server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server

# Application controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Repository server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

## 🔗 Integration with CI/CD

### GitHub Actions Integration

ArgoCD works with existing CI/CD by:

1. **CI**: Build and test (existing GitHub Actions)
2. **CD**: ArgoCD pulls from Git and deploys
3. **Separation**: Clear boundary between CI and CD

### Webhook Configuration (Optional)

For faster sync times, configure GitHub webhooks:

```bash
# Get ArgoCD webhook URL
kubectl get service argocd-server -n argocd

# Configure in GitHub repository settings
# Webhook URL: https://<argocd-server>/api/webhook
```

## 📚 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://www.gitops.tech/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

## 🎯 Success Criteria

- ✅ ArgoCD deployed and accessible
- ✅ Application syncs automatically on git push
- ✅ Rollback functionality working
- ✅ UI provides deployment history
- ✅ RBAC and security configured
- ✅ Monitoring and alerting integrated
