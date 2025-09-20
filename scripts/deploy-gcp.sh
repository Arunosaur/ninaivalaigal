#!/bin/bash
set -euo pipefail

# GCP deployment script for ninaivalaigal Apple Container CLI stack
# Deploys to Compute Engine instance

PROJECT_ID="${PROJECT_ID:-}"
ZONE="${ZONE:-us-central1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-medium}"
INSTANCE_NAME="${INSTANCE_NAME:-ninaivalaigal-stack}"
IMAGE_FAMILY="${IMAGE_FAMILY:-ubuntu-2204-lts}"
IMAGE_PROJECT="${IMAGE_PROJECT:-ubuntu-os-cloud}"

echo "🚀 Deploying ninaivalaigal to Google Cloud Platform"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo "Machine Type: $MACHINE_TYPE"
echo "Instance Name: $INSTANCE_NAME"
echo ""

# Check gcloud CLI
if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Validate project ID
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID is required"
    echo ""
    echo "Usage: PROJECT_ID=my-project ./scripts/deploy-gcp.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  ZONE          - GCP zone (default: us-central1-a)"
    echo "  MACHINE_TYPE  - Machine type (default: e2-medium)"
    echo "  INSTANCE_NAME - Instance name (default: ninaivalaigal-stack)"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 >/dev/null; then
    echo "❌ Not authenticated with gcloud. Please run:"
    echo "   gcloud auth login"
    exit 1
fi

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable compute.googleapis.com

# Create firewall rule for ninaivalaigal
echo "🔒 Creating firewall rule..."
if ! gcloud compute firewall-rules describe ninaivalaigal-allow-http >/dev/null 2>&1; then
    gcloud compute firewall-rules create ninaivalaigal-allow-http \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow HTTP traffic for ninaivalaigal"
fi

# Create startup script
cat > /tmp/ninaivalaigal-startup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Log all output
exec > >(tee -a /var/log/ninaivalaigal-startup.log)
exec 2>&1

echo "🚀 Starting ninaivalaigal setup on GCP..."

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y curl jq git make postgresql-client

# Install Podman (Apple Container CLI alternative for cloud)
apt-get install -y podman
ln -sf /usr/bin/podman /usr/local/bin/container

# Create ninaivalaigal user
useradd -m -s /bin/bash ninaivalaigal
usermod -aG sudo ninaivalaigal

# Clone ninaivalaigal repository
cd /home/ninaivalaigal
sudo -u ninaivalaigal git clone https://github.com/Arunosaur/ninaivalaigal.git

# Setup systemd service
cat > /etc/systemd/system/ninaivalaigal.service << 'SERVICE'
[Unit]
Description=Ninaivalaigal Stack
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=ninaivalaigal
WorkingDirectory=/home/ninaivalaigal/ninaivalaigal
ExecStart=/usr/bin/make dev-up
ExecStop=/usr/bin/make dev-down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
systemctl daemon-reload
systemctl enable ninaivalaigal
systemctl start ninaivalaigal

# Setup health check endpoint for GCP load balancer
apt-get install -y nginx
cat > /etc/nginx/sites-available/ninaivalaigal << 'NGINX'
server {
    listen 80;
    server_name _;

    location /health {
        proxy_pass http://localhost:13370/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:13370;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/ninaivalaigal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
systemctl enable nginx

echo "✅ Ninaivalaigal setup complete on GCP"
EOF

echo "🚀 Creating Compute Engine instance..."

# Create instance
gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,ninaivalaigal \
    --metadata-from-file startup-script=/tmp/ninaivalaigal-startup.sh

echo "✅ Instance created: $INSTANCE_NAME"
echo ""
echo "⏳ Waiting for instance to be ready..."

# Wait for instance to be running
sleep 10

# Get instance details
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

INTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --format="get(networkInterfaces[0].networkIP)")

echo "✅ Instance is running!"
echo ""
echo "📋 Instance Details:"
echo "   Instance Name: $INSTANCE_NAME"
echo "   External IP:   $EXTERNAL_IP"
echo "   Internal IP:   $INTERNAL_IP"
echo "   Zone:          $ZONE"
echo "   Project:       $PROJECT_ID"
echo ""
echo "🌍 Access URLs (available in ~2-3 minutes):"
echo "   API Health:    http://$EXTERNAL_IP/health"
echo "   API Docs:      http://$EXTERNAL_IP/docs"
echo "   API Metrics:   http://$EXTERNAL_IP/metrics"
echo ""
echo "🔐 SSH Access:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "📊 Monitor deployment:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u ninaivalaigal -f'"
echo ""
echo "🛑 To delete instance:"
echo "   gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE"

# Clean up temporary files
rm -f /tmp/ninaivalaigal-startup.sh

echo ""
echo "✨ GCP deployment complete! Instance is initializing ninaivalaigal stack."
