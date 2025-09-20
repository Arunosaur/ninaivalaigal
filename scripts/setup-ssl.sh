#!/bin/bash
set -euo pipefail

# SSL/TLS setup for ninaivalaigal stack
# Supports Let's Encrypt certificates and self-signed certificates

DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
CERT_TYPE="${CERT_TYPE:-letsencrypt}"  # letsencrypt or self-signed
NGINX_CONFIG_DIR="${NGINX_CONFIG_DIR:-/etc/nginx}"
CERT_DIR="${CERT_DIR:-/etc/ssl/certs/ninaivalaigal}"

echo "🔐 Setting up SSL/TLS for ninaivalaigal"
echo "======================================"
echo "Domain: $DOMAIN"
echo "Certificate Type: $CERT_TYPE"
echo ""

# Validate domain
if [ -z "$DOMAIN" ]; then
    echo "❌ Error: DOMAIN is required"
    echo ""
    echo "Usage examples:"
    echo "  # Let's Encrypt certificate"
    echo "  DOMAIN=api.mycompany.com EMAIL=admin@mycompany.com ./scripts/setup-ssl.sh"
    echo ""
    echo "  # Self-signed certificate"
    echo "  DOMAIN=localhost CERT_TYPE=self-signed ./scripts/setup-ssl.sh"
    echo ""
    echo "Environment variables:"
    echo "  DOMAIN     - Domain name (required)"
    echo "  EMAIL      - Email for Let's Encrypt (required for letsencrypt)"
    echo "  CERT_TYPE  - letsencrypt|self-signed (default: letsencrypt)"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Install required packages
echo "📦 Installing required packages..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Create certificate directory
mkdir -p "$CERT_DIR"

case "$CERT_TYPE" in
    "letsencrypt")
        if [ -z "$EMAIL" ]; then
            echo "❌ Error: EMAIL is required for Let's Encrypt certificates"
            exit 1
        fi

        echo "🔒 Obtaining Let's Encrypt certificate for $DOMAIN..."

        # Stop nginx temporarily
        systemctl stop nginx || true

        # Obtain certificate
        certbot certonly \
            --standalone \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            -d "$DOMAIN"

        CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

        echo "✅ Let's Encrypt certificate obtained"
        ;;

    "self-signed")
        echo "🔒 Creating self-signed certificate for $DOMAIN..."

        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$CERT_DIR/server.key" \
            -out "$CERT_DIR/server.crt" \
            -subj "/C=US/ST=CA/L=San Francisco/O=Ninaivalaigal/CN=$DOMAIN"

        CERT_PATH="$CERT_DIR/server.crt"
        KEY_PATH="$CERT_DIR/server.key"

        echo "✅ Self-signed certificate created"
        ;;

    *)
        echo "❌ Unknown certificate type: $CERT_TYPE"
        exit 1
        ;;
esac

# Create nginx configuration
echo "🌐 Configuring nginx..."

cat > "$NGINX_CONFIG_DIR/sites-available/ninaivalaigal-ssl" << EOF
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL configuration
    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Proxy to ninaivalaigal API
    location / {
        proxy_pass http://localhost:13370;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:13370/health;
        access_log off;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        proxy_pass http://localhost:13370/metrics;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
}
EOF

# Enable site
ln -sf "$NGINX_CONFIG_DIR/sites-available/ninaivalaigal-ssl" "$NGINX_CONFIG_DIR/sites-enabled/"
rm -f "$NGINX_CONFIG_DIR/sites-enabled/default"

# Test nginx configuration
nginx -t

# Start nginx
systemctl start nginx
systemctl enable nginx

# Setup certificate renewal for Let's Encrypt
if [ "$CERT_TYPE" = "letsencrypt" ]; then
    echo "🔄 Setting up automatic certificate renewal..."

    # Create renewal hook
    cat > /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh

    # Test renewal
    certbot renew --dry-run

    echo "✅ Automatic renewal configured"
fi

echo ""
echo "✅ SSL/TLS setup complete!"
echo ""
echo "🌍 Your ninaivalaigal stack is now available at:"
echo "   https://$DOMAIN"
echo ""
echo "🔒 SSL/TLS Details:"
echo "   Certificate: $CERT_PATH"
echo "   Private Key: $KEY_PATH"
echo "   Type: $CERT_TYPE"
echo ""
if [ "$CERT_TYPE" = "letsencrypt" ]; then
    echo "🔄 Certificate will auto-renew via cron"
    echo "   Test renewal: sudo certbot renew --dry-run"
fi
echo ""
echo "📊 Nginx status:"
echo "   sudo systemctl status nginx"
echo "   sudo nginx -t"
