#!/bin/bash
set -euo pipefail

# SPEC-021: ArgoCD Status and Management Script
# Shows ArgoCD and application status

echo "📊 ArgoCD Status Dashboard"
echo "=========================="

# Check if ArgoCD is installed
if ! kubectl get namespace argocd &> /dev/null; then
    echo "❌ ArgoCD namespace not found"
    echo "   Run: ./scripts/argocd-install.sh"
    exit 1
fi

# ArgoCD Server Status
echo ""
echo "🖥️  ArgoCD Server Status:"
kubectl get deployment argocd-server -n argocd -o custom-columns="NAME:.metadata.name,READY:.status.readyReplicas,AVAILABLE:.status.availableReplicas,AGE:.metadata.creationTimestamp" 2>/dev/null || echo "   Not deployed"

# ArgoCD Components Status
echo ""
echo "🔧 ArgoCD Components:"
kubectl get pods -n argocd -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[*].ready,AGE:.metadata.creationTimestamp" 2>/dev/null || echo "   No pods found"

# Applications Status
echo ""
echo "📱 ArgoCD Applications:"
if kubectl get applications -n argocd &> /dev/null; then
    kubectl get applications -n argocd -o custom-columns="NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision,AGE:.metadata.creationTimestamp" 2>/dev/null
else
    echo "   No applications found"
fi

# Ninaivalaigal Application Details
echo ""
echo "🎯 Ninaivalaigal Application Details:"
if kubectl get application ninaivalaigal -n argocd &> /dev/null; then
    APP_STATUS=$(kubectl get application ninaivalaigal -n argocd -o jsonpath='{.status}' 2>/dev/null)
    SYNC_STATUS=$(echo "$APP_STATUS" | jq -r '.sync.status // "Unknown"' 2>/dev/null || echo "Unknown")
    HEALTH_STATUS=$(echo "$APP_STATUS" | jq -r '.health.status // "Unknown"' 2>/dev/null || echo "Unknown")
    REVISION=$(echo "$APP_STATUS" | jq -r '.sync.revision // "Unknown"' 2>/dev/null || echo "Unknown")

    echo "   Sync Status: $SYNC_STATUS"
    echo "   Health Status: $HEALTH_STATUS"
    echo "   Revision: $REVISION"

    # Show recent sync operations
    echo ""
    echo "📋 Recent Operations:"
    kubectl get application ninaivalaigal -n argocd -o jsonpath='{.status.operationState}' 2>/dev/null | jq -r '.message // "No recent operations"' 2>/dev/null || echo "   No operation data"
else
    echo "   Application not found"
fi

# Port Forward Status
echo ""
echo "🌐 Port Forward Status:"
if pgrep -f "kubectl.*port-forward.*argocd-server" > /dev/null; then
    PID=$(pgrep -f "kubectl.*port-forward.*argocd-server")
    echo "   ✅ Running (PID: $PID)"
    echo "   🔗 Access: https://localhost:8080"
else
    echo "   ❌ Not running"
    echo "   💡 Start with: kubectl port-forward svc/argocd-server -n argocd 8080:443"
fi

# Show credentials if available
echo ""
echo "🔑 Access Credentials:"
if [[ -f "argocd/credentials.txt" ]]; then
    echo "   📄 Saved in: argocd/credentials.txt"
    echo "   👤 Username: admin"
    echo "   🔒 Password: (see credentials file)"
else
    echo "   ⚠️  Credentials file not found"
    echo "   💡 Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
fi

echo ""
echo "🛠️  Management Commands:"
echo "   Sync application: kubectl patch application ninaivalaigal -n argocd --type merge -p '{\"operation\":{\"sync\":{}}}'"
echo "   View logs: kubectl logs -n argocd deployment/argocd-server"
echo "   Restart ArgoCD: kubectl rollout restart deployment/argocd-server -n argocd"
echo ""
