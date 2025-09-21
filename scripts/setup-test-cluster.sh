#!/bin/bash
set -euo pipefail

# SPEC-021: Test Cluster Setup for ArgoCD Testing
# Creates a kind cluster and prepares it for ArgoCD deployment

CLUSTER_NAME="${CLUSTER_NAME:-ninaivalaigal-test}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🚀 Setting up test Kubernetes cluster for ArgoCD testing..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if cluster already exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "⚠️  Cluster '${CLUSTER_NAME}' already exists"
    echo "   Current context: $(kubectl config current-context)"

    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting existing cluster..."
        kind delete cluster --name "${CLUSTER_NAME}"
    else
        echo "✅ Using existing cluster"
        kubectl cluster-info --context "kind-${CLUSTER_NAME}"
        exit 0
    fi
fi

# Create kind cluster configuration
cat > "${PROJECT_ROOT}/kind-config.yaml" << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 8080
    hostPort: 8080
    protocol: TCP
EOF

echo "📦 Creating kind cluster '${CLUSTER_NAME}'..."
kind create cluster --config "${PROJECT_ROOT}/kind-config.yaml"

# Wait for cluster to be ready
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Install NGINX Ingress Controller (useful for testing)
echo "🌐 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
echo "⏳ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# Create ninaivalaigal namespace
echo "📦 Creating ninaivalaigal namespace..."
kubectl create namespace ninaivalaigal --dry-run=client -o yaml | kubectl apply -f -

# Show cluster info
echo ""
echo "🎉 Test cluster setup completed!"
echo ""
echo "📊 Cluster Information:"
echo "   Name: ${CLUSTER_NAME}"
echo "   Context: kind-${CLUSTER_NAME}"
echo "   Nodes: $(kubectl get nodes --no-headers | wc -l)"
echo "   Kubernetes Version: $(kubectl version --short --client=false | grep Server | awk '{print $3}')"
echo ""
echo "🔧 Available Services:"
kubectl get pods -A -o wide
echo ""
echo "🛠️  Next Steps:"
echo "   1. Install ArgoCD: make argocd-install"
echo "   2. Check status: make argocd-status"
echo "   3. Access UI: make argocd-ui"
echo ""
echo "🗑️  Cleanup: kind delete cluster --name ${CLUSTER_NAME}"
echo ""

# Save cluster info
cat > "${PROJECT_ROOT}/test-cluster-info.txt" << EOF
Test Cluster Information
========================
Name: ${CLUSTER_NAME}
Context: kind-${CLUSTER_NAME}
Created: $(date)

Management Commands:
- kubectl config use-context kind-${CLUSTER_NAME}
- kind delete cluster --name ${CLUSTER_NAME}
- kubectl get pods -A

ArgoCD Testing:
- make argocd-install
- make argocd-status
- make argocd-ui
EOF

echo "💾 Cluster info saved to: test-cluster-info.txt"
