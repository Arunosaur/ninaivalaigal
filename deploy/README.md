# mem0 Deployment Guide

This directory contains Ansible playbooks and configuration templates for deploying mem0 on a production VM with PostgreSQL, Nginx, and Supervisor.

## Prerequisites

1. **Target VM**: Ubuntu 20.04+ server with SSH access
2. **Ansible**: Install on your local machine (`pip install ansible`)
3. **SSH Key**: Set up SSH key-based authentication to your VM
4. **Domain/IP**: Have a domain name or static IP for your VM

## Quick Start

### 1. Configure Inventory

Edit `inventory.yml` with your server details:

```yaml
[mem0_servers]
mem0-vm ansible_host=YOUR_SERVER_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/your-key.pem

[mem0_servers:vars]
vault_postgres_password=your_secure_password_here
mem0_repo_url=https://github.com/your-org/mem0.git
mem0_version=main
```

### 2. Encrypt Sensitive Variables (Optional but Recommended)

```bash
ansible-vault encrypt_string 'your_secure_password' --name 'vault_postgres_password'
```

### 3. Deploy

```bash
# Test connectivity
ansible -i inventory.yml all -m ping

# Deploy mem0
ansible-playbook -i inventory.yml ansible-playbook.yml --ask-become-pass
```

## What Gets Deployed

### System Components
- **PostgreSQL 13**: Database server with dedicated `mem0` database
- **Python 3.9+**: Runtime environment with virtual environment
- **Nginx**: Reverse proxy with SSL-ready configuration
- **Supervisor**: Process manager for mem0 server
- **UFW Firewall**: Configured for HTTP/HTTPS/SSH access

### mem0 Components
- **Server**: FastAPI application with database backend
- **Configuration**: Production-ready `mem0.config.json`
- **Logging**: Centralized logs in `/var/log/mem0/`
- **Backup**: Daily PostgreSQL backups with rotation

### Directory Structure
```
/opt/mem0/
├── server/           # mem0 server code
├── client/           # mem0 client tools
├── logs/             # Application logs
├── backups/          # Database backups
└── venv/             # Python virtual environment
```

## Post-Deployment

### 1. Verify Services
```bash
# Check mem0 server status
sudo supervisorctl status mem0

# Check nginx status
sudo systemctl status nginx

# Check PostgreSQL status
sudo systemctl status postgresql
```

### 2. Test API
```bash
# Test server health
curl http://your-server-ip/

# Test with client
./client/mem0 context start test-deployment
```

### 3. Configure DNS (Optional)
Point your domain to the server IP and update nginx configuration for SSL.

## Configuration Files

### Templates
- `mem0.config.json.j2`: Production configuration with PostgreSQL
- `mem0-nginx.conf.j2`: Nginx reverse proxy configuration
- `mem0-supervisor.conf.j2`: Supervisor process configuration
- `backup-mem0.sh.j2`: Database backup script

### Variables
Key variables you can customize in `inventory.yml`:
- `vault_postgres_password`: PostgreSQL password
- `mem0_repo_url`: Git repository URL
- `mem0_version`: Git branch/tag to deploy
- `mem0_port`: Server port (default: 13370)
- `mem0_host`: Server bind address (default: 127.0.0.1)

## Maintenance

### Backup Management
```bash
# Manual backup
sudo /opt/mem0/backup-mem0.sh

# View backups
ls -la /opt/mem0/backups/
```

### Log Management
```bash
# View mem0 logs
sudo tail -f /var/log/mem0/mem0.log

# View nginx logs
sudo tail -f /var/log/nginx/mem0_access.log
```

### Updates
```bash
# Update mem0 code
ansible-playbook -i inventory.yml ansible-playbook.yml --tags update
```

## Security Notes

1. **Firewall**: Only HTTP, HTTPS, and SSH ports are open
2. **Database**: PostgreSQL only accepts local connections
3. **Passwords**: Use ansible-vault for sensitive data
4. **SSL**: Configure SSL certificates for production use
5. **Backups**: Stored locally - consider remote backup storage

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
sudo supervisorctl tail mem0 stderr
sudo journalctl -u nginx -f
```

**Database connection issues:**
```bash
sudo -u postgres psql -d mem0db -c "SELECT version();"
```

**Permission issues:**
```bash
sudo chown -R mem0:mem0 /opt/mem0/
```

### Support
Check logs in `/var/log/mem0/` and `/var/log/nginx/` for detailed error information.
