# Remote Access & Cloud Deployment Guide

This guide covers deploying and accessing your ninaivalaigal Apple Container CLI stack remotely.

## 🌐 Remote Access Options

### 1. SSH Tunneling (Recommended)

Securely expose your local stack to remote users:

```bash
# Start SSH tunnel to cloud server
REMOTE_HOST=my-server.com make tunnel-start

# Stop tunnels
make tunnel-stop
```

**Features:**
- ✅ Secure encrypted connection
- ✅ No firewall changes needed
- ✅ Works with any SSH server
- ✅ Multiple service tunneling (API, DB, PgBouncer)

**Requirements:**
- SSH access to remote server
- SSH key configured (`~/.ssh/id_rsa`)

### 2. Direct Cloud Deployment

Deploy directly to cloud providers:

```bash
# Deploy to AWS
KEY_NAME=my-key make deploy-aws

# Deploy to Google Cloud
PROJECT_ID=my-project make deploy-gcp

# Deploy to Microsoft Azure
RESOURCE_GROUP=my-rg make deploy-azure

# Setup secure tunnel for remote access
REMOTE_HOST=server.com make tunnel-start
```

## ☁️ Cloud Deployment

### AWS Deployment

**Prerequisites:**
- AWS CLI installed (`brew install awscli`)
- AWS credentials configured (`aws configure`)
- EC2 key pair created

**Quick Start:**
```bash
# Deploy to AWS
KEY_NAME=my-key-pair AWS_REGION=us-west-2 make deploy-aws

# Monitor deployment
aws logs tail /aws/ec2/ninaivalaigal --follow
```

**What gets deployed:**
- ✅ EC2 instance (t3.medium, Ubuntu 22.04 ARM64)
- ✅ Security group with ports 22, 8080
- ✅ Automatic ninaivalaigal stack setup
- ✅ Systemd service for auto-restart
- ✅ Log rotation configured

**Access:**
```bash
# SSH to instance
aws ec2 describe-instances --filters "Name=tag:Name,Values=ninaivalaigal-stack"

# Get public IP and SSH
ssh -i ~/.ssh/my-key-pair.pem ubuntu@<PUBLIC_IP>
```

### Google Cloud Deployment

**Prerequisites:**
- gcloud CLI installed
- GCP project created and billing enabled
- Authentication configured (`gcloud auth login`)

**Quick Start:**
```bash
# Deploy to GCP
PROJECT_ID=my-project-id ZONE=us-central1-a make deploy-gcp

# Monitor deployment
gcloud compute ssh ninaivalaigal-stack --zone=us-central1-a --command='sudo journalctl -u ninaivalaigal -f'
```

### Microsoft Azure Deployment

**Prerequisites:**
- Azure CLI installed (`brew install azure-cli`)
- Azure subscription and authentication (`az login`)
- Resource group created or will be created automatically

**Quick Start:**
```bash
# Deploy to Azure VM
RESOURCE_GROUP=my-rg LOCATION=eastus make deploy-azure

# Deploy to Azure Container Instances (simplified)
RESOURCE_GROUP=my-rg DEPLOYMENT_TYPE=aci make deploy-azure

# Monitor deployment
az vm run-command invoke --resource-group my-rg --name ninaivalaigal-vm --command-id RunShellScript --scripts "sudo journalctl -u ninaivalaigal -f"
```

**What gets deployed:**
- ✅ Azure VM (Standard_B2s, Ubuntu 22.04)
- ✅ Network Security Group with ports 22, 8080
- ✅ Automatic ninaivalaigal stack setup via cloud-init
- ✅ Nginx reverse proxy configuration
- ✅ Systemd service for auto-restart

**Access:**
```bash
# SSH to VM
az vm show --resource-group my-rg --name ninaivalaigal-vm --show-details --query publicIps -o tsv

# SSH with IP
ssh azureuser@<PUBLIC_IP>
```

**What gets deployed:**
- ✅ Compute Engine instance (e2-medium, Ubuntu 22.04)
- ✅ Firewall rule for HTTP traffic
- ✅ Nginx reverse proxy with health checks
- ✅ Automatic ninaivalaigal stack setup
- ✅ Systemd service configuration

## 🔐 SSL/TLS Configuration

### Let's Encrypt (Production)

```bash
# Setup SSL with Let's Encrypt
sudo DOMAIN=api.mycompany.com EMAIL=admin@mycompany.com ./scripts/setup-ssl.sh

# Verify certificate
curl -I https://api.mycompany.com/health
```

### Self-Signed (Development)

```bash
# Setup self-signed SSL
sudo DOMAIN=localhost CERT_TYPE=self-signed ./scripts/setup-ssl.sh

# Test with curl (ignore certificate warning)
curl -k https://localhost/health
```

**SSL Features:**
- ✅ Modern TLS 1.2/1.3 configuration
- ✅ Security headers (HSTS, XSS protection)
- ✅ Automatic HTTP → HTTPS redirect
- ✅ WebSocket support
- ✅ Automatic certificate renewal (Let's Encrypt)

## 🏗️ Architecture Patterns

### Single Instance Deployment

```
Internet → Load Balancer → nginx → ninaivalaigal API → PgBouncer → PostgreSQL
```

**Use cases:**
- Development/staging environments
- Small to medium workloads
- Cost-effective deployment

### Multi-Instance Deployment

```
Internet → Load Balancer → [nginx + ninaivalaigal] × N → Shared PgBouncer → PostgreSQL
```

**Use cases:**
- High availability requirements
- Large scale deployments
- Geographic distribution

## 📊 Monitoring & Logging

### Health Checks

```bash
# Basic health check
curl https://your-domain.com/health

# Detailed health with metrics
curl https://your-domain.com/health/detailed

# Prometheus metrics
curl https://your-domain.com/metrics
```

### Log Access

```bash
# Application logs
sudo journalctl -u ninaivalaigal -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# SSL certificate logs
sudo journalctl -u certbot -f
```

### Performance Monitoring

```bash
# Container resource usage
container stats

# Database connections
psql "postgresql://nina:change_me_securely@localhost:5432/nina" -c "SELECT count(*) FROM pg_stat_activity;"  # pragma: allowlist secret

# PgBouncer stats
psql "postgresql://nina:change_me_securely@localhost:6432/pgbouncer" -c "SHOW STATS;"  # pragma: allowlist secret
```

## 🔧 Troubleshooting

### Common Issues

**1. SSH Tunnel Connection Refused**
```bash
# Check SSH connectivity
ssh -i ~/.ssh/id_rsa ubuntu@remote-host exit

# Check local stack
make health

# Verify tunnel processes
ps aux | grep ssh
```

**2. Cloud Instance Not Responding**
```bash
# AWS: Check instance status
aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# GCP: Check instance status
gcloud compute instances describe ninaivalaigal-stack --zone=us-central1-a

# Check startup logs
sudo journalctl -u ninaivalaigal -n 50
```

**3. SSL Certificate Issues**
```bash
# Test certificate
openssl s_client -connect your-domain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew

# Check nginx configuration
sudo nginx -t
```

### Performance Optimization

**Database Tuning:**
```sql
-- Optimize PostgreSQL for cloud deployment
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

**PgBouncer Tuning:**
```ini
# Increase connection pool size
max_client_conn = 200
default_pool_size = 25
server_lifetime = 3600
```

**Nginx Tuning:**
```nginx
# Optimize for high traffic
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
client_max_body_size 10M;
```

## 🛡️ Security Best Practices

### Network Security

1. **Firewall Configuration:**
   - Only expose necessary ports (80, 443, 22)
   - Use security groups/firewall rules
   - Restrict SSH access to known IPs

2. **SSL/TLS:**
   - Always use HTTPS in production
   - Enable HSTS headers
   - Use strong cipher suites

3. **Access Control:**
   - Rotate SSH keys regularly
   - Use IAM roles for cloud access
   - Enable audit logging

### Application Security

1. **Database Security:**
   - Use strong passwords
   - Enable connection encryption
   - Restrict database access to application only

2. **API Security:**
   - Enable JWT authentication
   - Rate limiting
   - Input validation

3. **Container Security:**
   - Use non-root users
   - Scan images for vulnerabilities
   - Keep base images updated

## 📈 Scaling Strategies

### Vertical Scaling

```bash
# AWS: Change instance type
aws ec2 modify-instance-attribute --instance-id i-1234567890abcdef0 --instance-type t3.large

# GCP: Change machine type
gcloud compute instances set-machine-type ninaivalaigal-stack --machine-type e2-standard-2 --zone us-central1-a
```

### Horizontal Scaling

1. **Load Balancer Setup:**
   - AWS Application Load Balancer
   - GCP Load Balancer
   - Nginx upstream configuration

2. **Database Scaling:**
   - Read replicas for read-heavy workloads
   - Connection pooling optimization
   - Database sharding for write scaling

3. **Container Orchestration:**
   - Kubernetes deployment
   - Docker Swarm
   - Nomad scheduling

## 🚀 Next Steps

1. **Production Hardening:**
   - Implement backup strategies
   - Set up monitoring alerts
   - Configure log aggregation

2. **CI/CD Integration:**
   - Automated deployments
   - Blue-green deployments
   - Canary releases

3. **Advanced Features:**
   - Multi-region deployment
   - Auto-scaling policies
   - Disaster recovery planning

---

**Need Help?**
- Check the [troubleshooting section](#-troubleshooting)
- Review logs: `sudo journalctl -u ninaivalaigal -f`
- Test connectivity: `make health`
