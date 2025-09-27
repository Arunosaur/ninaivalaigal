# Production Deployment Guide - Ninaivalaigal with RBAC

## Overview
This guide provides comprehensive instructions for deploying the Ninaivalaigal platform with integrated RBAC system to production environments.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 50GB minimum, SSD recommended
- **Network**: HTTPS/TLS certificate required

### Dependencies
```bash
# System packages
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql-15 nginx redis-server

# Python packages (from requirements.txt)
pip install -r server/requirements.txt
```

## Database Setup

### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE mem0db;
CREATE USER mem0user WITH ENCRYPTED PASSWORD 'your_secure_password  # pragma: allowlist secret';
GRANT ALL PRIVILEGES ON DATABASE mem0db TO mem0user;

-- Connect to mem0db and grant schema permissions
\c mem0db
GRANT ALL ON SCHEMA public TO mem0user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mem0user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mem0user;
```

### Database Migration
```bash
# Run core database setup
python server/database.py

# Run RBAC migration
psql -U mem0user -d mem0db -f scripts/create_rbac_tables.sql

# Verify tables
psql -U mem0user -d mem0db -c "\dt"
```

## Environment Configuration

### Required Environment Variables
```bash
# Create production environment file
cat > /opt/ninaivalaigal/.env << EOF
# Database
NINAIVALAIGAL_DATABASE_URL=postgresql://mem0user:your_secure_password  # pragma: allowlist secret@localhost:5432/mem0db

# JWT Security
NINAIVALAIGAL_JWT_SECRET=your_256_bit_secret_key_here

# MCP Server
NINAIVALAIGAL_USER_TOKEN=your_mcp_server_token  # pragma: allowlist secret

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Performance
WORKERS=4
MAX_CONNECTIONS=100
CONNECTION_TIMEOUT=30
EOF
```

### Security Configuration
```bash
# Set secure file permissions
chmod 600 /opt/ninaivalaigal/.env
chown ninaivalaigal:ninaivalaigal /opt/ninaivalaigal/.env

# Generate secure JWT secret
python -c "import secrets; print(secrets.token  # pragma: allowlist secret_urlsafe(32))"
```

## Application Deployment

### Directory Structure
```
/opt/ninaivalaigal/
├── server/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── index.html
│   └── ...
├── logs/
├── backups/
└── .env
```

### Systemd Service Configuration
```ini
# /etc/systemd/system/ninaivalaigal.service
[Unit]
Description=Ninaivalaigal Memory Platform
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=ninaivalaigal
Group=ninaivalaigal
WorkingDirectory=/opt/ninaivalaigal/server
Environment=PATH=/opt/ninaivalaigal/venv/bin
EnvironmentFile=/opt/ninaivalaigal/.env
ExecStart=/opt/ninaivalaigal/venv/bin/uvicorn main:app --host 0.0.0.0 --port 13370 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/ninaivalaigal/logs /opt/ninaivalaigal/backups

[Install]
WantedBy=multi-user.target
```

### Service Management
```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ninaivalaigal
sudo systemctl start ninaivalaigal

# Check status
sudo systemctl status ninaivalaigal

# View logs
sudo journalctl -u ninaivalaigal -f
```

## Nginx Configuration

### Reverse Proxy Setup
```nginx
# /etc/nginx/sites-available/ninaivalaigal
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # API Endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:13370;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static Files
    location / {
        root /opt/ninaivalaigal/frontend;
        try_files $uri $uri/ /index.html;

        # Caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:13370/health;
        access_log off;
    }
}
```

### Enable Configuration
```bash
sudo ln -s /etc/nginx/sites-available/ninaivalaigal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/TLS Certificate

### Let's Encrypt Setup
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### Log Configuration
```python
# server/logging_config.py
import logging
import logging.handlers
import os

def setup_logging():
    log_dir = "/opt/ninaivalaigal/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Application logs
    app_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # Security logs
    security_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/security.log",
        maxBytes=10*1024*1024,
        backupCount=10
    )

    # RBAC audit logs
    rbac_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/rbac_audit.log",
        maxBytes=10*1024*1024,
        backupCount=10
    )

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[app_handler]
    )
```

### Health Monitoring
```bash
# Create monitoring script
cat > /opt/ninaivalaigal/scripts/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:13370/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): Service healthy"
    exit 0
else
    echo "$(date): Service unhealthy (HTTP $RESPONSE)"
    systemctl restart ninaivalaigal
    exit 1
fi
EOF

chmod +x /opt/ninaivalaigal/scripts/health_check.sh

# Add to crontab
echo "*/5 * * * * /opt/ninaivalaigal/scripts/health_check.sh >> /opt/ninaivalaigal/logs/health.log 2>&1" | crontab -
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
cat > /opt/ninaivalaigal/scripts/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/ninaivalaigal/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mem0db_$DATE.sql"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U mem0user -h localhost mem0db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "$(date): Database backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /opt/ninaivalaigal/scripts/backup_db.sh

# Schedule daily backups
echo "0 2 * * * /opt/ninaivalaigal/scripts/backup_db.sh >> /opt/ninaivalaigal/logs/backup.log 2>&1" | crontab -
```

### Application Backup
```bash
# Backup application files
tar -czf /opt/ninaivalaigal/backups/app_$(date +%Y%m%d).tar.gz \
    /opt/ninaivalaigal/server \
    /opt/ninaivalaigal/frontend \
    /opt/ninaivalaigal/.env
```

## Security Hardening

### Firewall Configuration
```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### System Security
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Enable fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Set up log monitoring
sudo apt install logwatch
```

## Performance Optimization

### Database Tuning
```sql
-- PostgreSQL configuration optimizations
-- Add to /etc/postgresql/15/main/postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Application Tuning
```python
# server/config.py
import os

class ProductionConfig:
    # Database connection pooling
    DATABASE_POOL_SIZE = 20
    DATABASE_POOL_OVERFLOW = 30
    DATABASE_POOL_TIMEOUT = 30

    # Caching
    REDIS_URL = "redis://localhost:6379/0"
    CACHE_TIMEOUT = 300

    # Rate limiting
    RATE_LIMIT_STORAGE_URL = "redis://localhost:6379/1"

    # Performance
    WORKERS = os.cpu_count() * 2
    WORKER_CONNECTIONS = 1000
```

## Deployment Checklist

### Pre-Deployment
- [ ] Database setup and migration completed
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup completed

### Deployment
- [ ] Application deployed to production directory
- [ ] Systemd service configured and started
- [ ] Nginx configuration applied
- [ ] Health checks passing
- [ ] RBAC system functional
- [ ] Authentication working

### Post-Deployment
- [ ] Performance monitoring active
- [ ] Log rotation configured
- [ ] Backup verification completed
- [ ] Security scan performed
- [ ] Documentation updated
- [ ] Team training completed

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
sudo journalctl -u ninaivalaigal -n 50

# Check configuration
sudo -u ninaivalaigal /opt/ninaivalaigal/venv/bin/python /opt/ninaivalaigal/server/main.py
```

#### Database Connection Issues
```bash
# Test database connection
psql -U mem0user -h localhost -d mem0db -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### RBAC Permission Issues
```bash
# Check RBAC tables
psql -U mem0user -d mem0db -c "SELECT * FROM role_assignments LIMIT 5;"

# Verify JWT token  # pragma: allowlist secret
python -c "
import jwt
token  # pragma: allowlist secret = 'your_jwt_token_here'
secret = 'your_jwt_secret'
print(jwt.decode(token  # pragma: allowlist secret, secret, algorithms=['HS256']))
"
```

### Performance Issues
- Monitor CPU and memory usage
- Check database query performance
- Review application logs for bottlenecks
- Verify network connectivity

### Security Incidents
- Check security logs in `/opt/ninaivalaigal/logs/security.log`
- Review RBAC audit logs
- Verify SSL certificate validity
- Check for unauthorized access attempts

## Maintenance

### Regular Tasks
- **Daily**: Check health status, review logs
- **Weekly**: Update system packages, review security logs
- **Monthly**: Database maintenance, backup verification
- **Quarterly**: Security audit, performance review

### Updates
```bash
# Application updates
cd /opt/ninaivalaigal
git pull origin main
sudo systemctl restart ninaivalaigal

# System updates
sudo apt update && sudo apt upgrade
sudo systemctl reboot
```

This production deployment guide ensures a secure, scalable, and maintainable Ninaivalaigal platform with comprehensive RBAC integration.
