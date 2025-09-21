# Production Deployment Guide

## 🎯 Production Overview

Enterprise-grade deployment guide for ninaivalaigal platform with high availability, scalability, and security.

## 🏗️ Production Architecture

### Infrastructure Components
- **Database**: PostgreSQL 15.14 + pgvector (HA cluster)
- **Cache**: Redis 7.4+ (cluster mode)
- **API**: FastAPI (multi-instance with load balancing)
- **Frontend**: React SPA (CDN distributed)
- **Proxy**: NGINX (SSL termination, load balancing)

### Deployment Targets
- **Kubernetes**: Primary production platform
- **Docker Compose**: Development and staging
- **Apple Container CLI**: Local development
- **Cloud Providers**: AWS, GCP, Azure support

## 🚀 Production Deployment Steps

### Phase 1: Infrastructure Preparation
```bash
# Provision infrastructure
terraform apply -var-file="production.tfvars"

# Configure Kubernetes cluster
kubectl apply -f k8s/production/

# Deploy monitoring stack
helm install prometheus prometheus-community/kube-prometheus-stack
```

### Phase 2: Database Deployment
```bash
# Deploy PostgreSQL cluster
kubectl apply -f k8s/database/postgresql-ha.yaml

# Initialize database schema
kubectl exec -it postgres-primary -- psql -f /scripts/init.sql

# Verify pgvector extension
kubectl exec -it postgres-primary -- psql -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Phase 3: Application Deployment
```bash
# Deploy Redis cluster
kubectl apply -f k8s/cache/redis-cluster.yaml

# Deploy API services
kubectl apply -f k8s/api/

# Deploy frontend
kubectl apply -f k8s/frontend/

# Configure ingress
kubectl apply -f k8s/ingress/
```

## 📊 Production Validation

### Health Check Validation
```bash
# API health endpoints
curl https://api.ninaivalaigal.com/health
curl https://api.ninaivalaigal.com/health/detailed
curl https://api.ninaivalaigal.com/metrics

# Database connectivity
kubectl exec -it postgres-primary -- pg_isready

# Redis cluster status
kubectl exec -it redis-0 -- redis-cli cluster info
```

### Performance Benchmarks
- **API Response Time**: P95 < 200ms
- **Database Queries**: P99 < 100ms
- **Memory Operations**: P95 < 1ms
- **Throughput**: 10,000+ requests/minute
- **Concurrent Users**: 5,000+ simultaneous

## 🔒 Production Security

### Security Configuration
```yaml
# Security policies
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-config
data:
  JWT_SECRET: ${JWT_SECRET}
  REDIS_PASSWORD: ${REDIS_PASSWORD}
  DATABASE_URL: ${DATABASE_URL}
  CORS_ORIGINS: "https://ninaivalaigal.com"
  RATE_LIMIT: "1000/hour"
```

### TLS Configuration
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Configure Let's Encrypt
kubectl apply -f k8s/tls/letsencrypt-issuer.yaml

# Verify certificates
kubectl get certificates -A
```

## 📈 Monitoring & Observability

### Prometheus Metrics
- **Application Metrics**: Request rate, error rate, duration
- **Infrastructure Metrics**: CPU, memory, disk, network
- **Business Metrics**: User activity, memory operations
- **SLO Metrics**: Availability, latency, error budget

### Grafana Dashboards
```bash
# Import production dashboards
kubectl apply -f monitoring/grafana/dashboards/

# Configure alerts
kubectl apply -f monitoring/prometheus/alerts/
```

### Log Aggregation
```bash
# Deploy ELK stack
helm install elasticsearch elastic/elasticsearch
helm install kibana elastic/kibana
helm install filebeat elastic/filebeat
```

## 🔄 Backup & Disaster Recovery

### Automated Backups
```bash
# Database backups (every 6 hours)
kubectl create cronjob postgres-backup --image=postgres:15 --schedule="0 */6 * * *"

# Redis snapshots (daily)
kubectl create cronjob redis-backup --image=redis:7 --schedule="0 2 * * *"

# Application data backups
kubectl apply -f k8s/backup/velero.yaml
```

### Disaster Recovery Plan
- **RTO**: 15 minutes (Recovery Time Objective)
- **RPO**: 1 hour (Recovery Point Objective)
- **Backup Retention**: 30 days local, 90 days cloud
- **Failover**: Automated with health checks

## 🎯 Production Checklist

### ✅ Pre-Production
- [ ] Infrastructure provisioned and configured
- [ ] Security policies implemented
- [ ] Monitoring and alerting configured
- [ ] Backup systems operational
- [ ] Load testing completed
- [ ] Security audit passed

### ✅ Production Deployment
- [ ] All services deployed and healthy
- [ ] DNS and TLS configured
- [ ] Performance benchmarks met
- [ ] Monitoring dashboards operational
- [ ] Backup verification completed

### ✅ Post-Production
- [ ] User acceptance testing passed
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Incident response procedures tested
- [ ] Performance monitoring active

## 🚨 Incident Response

### Escalation Matrix
1. **Level 1**: Automated alerts and self-healing
2. **Level 2**: On-call engineer response (5 minutes)
3. **Level 3**: Senior engineer escalation (15 minutes)
4. **Level 4**: Management and external support

### Common Issues & Solutions
- **Database Connection Issues**: Check connection pool limits
- **Redis Cache Misses**: Verify cache warming strategies
- **API Rate Limiting**: Review rate limit configurations
- **Memory Leaks**: Monitor container resource usage

## 📚 Related Documentation

- [Kubernetes Deployment](../kubernetes/README.md)
- [Security Configuration](../../security/README.md)
- [Monitoring Setup](../../runbooks/README.md)
- [API Documentation](../../api/README.md)

---

**Status**: ✅ Production Ready | **Scale**: Enterprise | **Availability**: 99.9% SLO
