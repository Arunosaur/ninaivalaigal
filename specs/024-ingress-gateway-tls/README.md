---
title: Untitled SPEC
---


# SPEC-024: Ingress Gateway and TLS Automation

## Title
HTTP Routing and Secure Access via TLS

## Objective
Serve `ninaivalaigal-api` securely via domain with TLS.

## Features

- Ingress controller (NGINX, Istio, or ALB)
- `ingress.yaml` for `ninaivalaigal-api`
- Auto-provision TLS via `cert-manager`
- Integration with Cloudflare or native DNS

## Implementation Targets

- ACME challenge automation
- HTTP to HTTPS redirect
- Path-based routing for future APIs

## Technical Requirements

### Ingress Controller Installation
```yaml
# ingress/nginx-controller.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
---
# NGINX Ingress Controller via Helm
```

### Cert-Manager Setup
```yaml
# tls/cert-manager.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@ninaivalaigal.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Application Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ninaivalaigal-ingress
  namespace: ninaivalaigal
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
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

### DNS Integration
- Cloudflare API for automatic DNS record management
- Route53 integration for AWS deployments
- Automatic subdomain provisioning for environments

## Success Criteria
- [ ] HTTPS endpoint accessible via custom domain
- [ ] Automatic TLS certificate renewal
- [ ] HTTP to HTTPS redirect working
- [ ] Path-based routing for multiple services

## Status
📋 Planned

---

## Related Documentation

### Components
- **NGINX Ingress Controller:** K8s HTTP/HTTPS routing
- **cert-manager:** Automated TLS certificate management
- **Let's Encrypt:** Free TLS certificates with auto-renewal

### Related SPECs
- **SPEC-021:** GitOps with ArgoCD (ingress deployment via GitOps)
- **SPEC-015:** Kubernetes Deployment Strategy (service exposure)
- **SPEC-023:** Secrets Management (TLS certificate storage)

### Taiga Tracking
- **US#154:** SPEC-024 Ingress Gateway and TLS Automation

---

## Implementation Status

📋 **PLANNED** - Not yet implemented

**Prerequisites:**
- Kubernetes cluster operational
- Domain name available (api.ninaivalaigal.com)
- DNS provider access (Cloudflare or Route53)

**Estimated Effort:** 2-3 weeks

---

**Last Updated:** October 30, 2025 (Taiga tracking added)
**Status:** Tracked in Taiga US#154
