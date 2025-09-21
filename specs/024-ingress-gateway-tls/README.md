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
