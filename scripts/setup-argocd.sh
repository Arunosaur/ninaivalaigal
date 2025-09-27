#!/bin/bash
set -euo pipefail

# Setup ArgoCD for GitOps Deployment
# This script installs and configures ArgoCD for the Ninaivalaigal project

echo "🚀 Setting up ArgoCD for GitOps deployment..."

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_status "ERROR" "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if we can connect to Kubernetes cluster
if ! kubectl cluster-info &> /dev/null; then
    print_status "ERROR" "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

print_status "SUCCESS" "Connected to Kubernetes cluster"

# Create ArgoCD namespace
print_status "INFO" "Creating ArgoCD namespace..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
print_status "INFO" "Installing ArgoCD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
print_status "INFO" "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get ArgoCD admin password
print_status "INFO" "Getting ArgoCD admin password..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Create port-forward to access ArgoCD UI (in background)
print_status "INFO" "Setting up port-forward to ArgoCD UI..."
kubectl port-forward svc/argocd-server -n argocd 8080:443 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

# Wait a moment for port-forward to establish
sleep 5

# Install ArgoCD CLI
print_status "INFO" "Installing ArgoCD CLI..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install argocd
    else
        curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-darwin-amd64
        chmod +x /usr/local/bin/argocd
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    chmod +x /usr/local/bin/argocd
fi

# Login to ArgoCD
print_status "INFO" "Logging into ArgoCD..."
argocd login localhost:8080 --username admin --password "$ARGOCD_PASSWORD" --insecure

# Apply ArgoCD project and applications
print_status "INFO" "Creating ArgoCD project and applications..."
kubectl apply -f k8s/argocd/projects/ninaivalaigal.yaml
kubectl apply -f k8s/argocd/applications/ninaivalaigal-dev.yaml

# Create additional environments if they exist
if [ -f "k8s/argocd/applications/ninaivalaigal-staging.yaml" ]; then
    kubectl apply -f k8s/argocd/applications/ninaivalaigal-staging.yaml
fi

if [ -f "k8s/argocd/applications/ninaivalaigal-prod.yaml" ]; then
    kubectl apply -f k8s/argocd/applications/ninaivalaigal-prod.yaml
fi

# Configure ArgoCD for GitHub integration
print_status "INFO" "Configuring GitHub integration..."
argocd repo add https://github.com/Arunosaur/ninaivalaigal.git --type git

# Sync the development application
print_status "INFO" "Syncing development application..."
argocd app sync ninaivalaigal-dev

# Kill the port-forward process
kill $PORT_FORWARD_PID 2>/dev/null || true

print_status "SUCCESS" "ArgoCD setup complete!"
print_status "INFO" "ArgoCD UI: https://localhost:8080"
print_status "INFO" "Username: admin"
print_status "INFO" "Password: $ARGOCD_PASSWORD"
print_status "INFO" ""
print_status "INFO" "To access ArgoCD UI, run:"
print_status "INFO" "kubectl port-forward svc/argocd-server -n argocd 8080:443"
print_status "INFO" ""
print_status "INFO" "Applications created:"
print_status "INFO" "- ninaivalaigal-dev (development environment)"

echo ""
echo "🎊 GitOps with ArgoCD is now ready!"
echo "Your applications will automatically sync when you push changes to the repository."
