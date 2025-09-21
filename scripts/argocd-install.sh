#!/bin/bash
set -euo pipefail

# SPEC-021: ArgoCD Installation Script
# Installs ArgoCD and configures GitOps for ninaivalaigal

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARGOCD_VERSION="${ARGOCD_VERSION:-v2.9.3}"

echo "🚀 Installing ArgoCD for ninaivalaigal GitOps..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed"
    exit 1
fi

# Check if we can connect to Kubernetes cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "   Make sure your kubeconfig is set up correctly"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster: $(kubectl config current-context)"

# Create argocd namespace
echo "📦 Creating argocd namespace..."
kubectl apply -f "${PROJECT_ROOT}/argocd/namespace.yaml"

# Install ArgoCD
echo "🔧 Installing ArgoCD ${ARGOCD_VERSION}..."
kubectl apply -n argocd -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"

# Wait for ArgoCD to be ready
echo "⏳ Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-repo-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-dex-server -n argocd

# Get initial admin password
echo "🔑 Getting ArgoCD admin password..."
ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Apply ninaivalaigal application
echo "📱 Creating ninaivalaigal ArgoCD application..."
kubectl apply -f "${PROJECT_ROOT}/argocd/application.yaml"

# Check if port-forward is already running
if pgrep -f "kubectl.*port-forward.*argocd-server" > /dev/null; then
    echo "⚠️  ArgoCD port-forward already running"
else
    echo "🌐 Starting ArgoCD UI port-forward..."
    kubectl port-forward svc/argocd-server -n argocd 8080:443 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    echo "   Port-forward PID: ${PORT_FORWARD_PID}"
fi

echo ""
echo "🎉 ArgoCD installation completed!"
echo ""
echo "📊 Access Information:"
echo "   URL: https://localhost:8080"
echo "   Username: admin"
echo "   Password: ${ADMIN_PASSWORD}"
echo ""
echo "🔧 Management Commands:"
echo "   View applications: kubectl get applications -n argocd"
echo "   View sync status: kubectl get application ninaivalaigal -n argocd -o yaml"
echo "   Stop port-forward: pkill -f 'kubectl.*port-forward.*argocd-server'"
echo ""
echo "📚 Next Steps:"
echo "   1. Access ArgoCD UI at https://localhost:8080"
echo "   2. Login with admin credentials above"
echo "   3. Check ninaivalaigal application sync status"
echo "   4. Make a change to k8s/ directory and watch auto-sync"
echo ""

# Save credentials for later use
cat > "${PROJECT_ROOT}/argocd/credentials.txt" << EOF
ArgoCD Access Information
========================
URL: https://localhost:8080
Username: admin
Password: ${ADMIN_PASSWORD}

Generated: $(date)
Cluster: $(kubectl config current-context)
EOF

echo "💾 Credentials saved to: argocd/credentials.txt"
echo "⚠️  Keep this file secure and do not commit to git!"
