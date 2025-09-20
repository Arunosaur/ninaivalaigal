#!/bin/bash
set -euo pipefail

# AWS deployment script for ninaivalaigal Apple Container CLI stack
# Deploys to EC2 instance with Apple Container CLI support

AWS_REGION="${AWS_REGION:-us-west-2}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
KEY_NAME="${KEY_NAME:-}"
SECURITY_GROUP="${SECURITY_GROUP:-}"
SUBNET_ID="${SUBNET_ID:-}"
AMI_ID="${AMI_ID:-}"  # Will auto-detect Ubuntu 22.04 ARM64 if not provided
INSTANCE_NAME="${INSTANCE_NAME:-ninaivalaigal-stack}"

echo "🚀 Deploying ninaivalaigal to AWS"
echo "================================="
echo "Region: $AWS_REGION"
echo "Instance Type: $INSTANCE_TYPE"
echo "Instance Name: $INSTANCE_NAME"
echo ""

# Check AWS CLI
if ! command -v aws >/dev/null 2>&1; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   brew install awscli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

# Validate required parameters
if [ -z "$KEY_NAME" ]; then
    echo "❌ Error: KEY_NAME is required"
    echo ""
    echo "Usage: KEY_NAME=my-key-pair ./scripts/deploy-aws.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  AWS_REGION      - AWS region (default: us-west-2)"
    echo "  INSTANCE_TYPE   - EC2 instance type (default: t3.medium)"
    echo "  SECURITY_GROUP  - Security group ID (will create if not provided)"
    echo "  SUBNET_ID       - Subnet ID (will use default VPC if not provided)"
    echo "  AMI_ID          - AMI ID (will auto-detect Ubuntu 22.04 ARM64)"
    exit 1
fi

# Auto-detect AMI if not provided
if [ -z "$AMI_ID" ]; then
    echo "🔍 Auto-detecting Ubuntu 22.04 ARM64 AMI..."
    AMI_ID=$(aws ec2 describe-images \
        --region "$AWS_REGION" \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
    echo "✅ Found AMI: $AMI_ID"
fi

# Create security group if not provided
if [ -z "$SECURITY_GROUP" ]; then
    echo "🔒 Creating security group..."
    SECURITY_GROUP=$(aws ec2 create-security-group \
        --region "$AWS_REGION" \
        --group-name "ninaivalaigal-sg" \
        --description "Security group for ninaivalaigal stack" \
        --query 'GroupId' \
        --output text)

    # Add rules for ninaivalaigal ports
    aws ec2 authorize-security-group-ingress \
        --region "$AWS_REGION" \
        --group-id "$SECURITY_GROUP" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

    aws ec2 authorize-security-group-ingress \
        --region "$AWS_REGION" \
        --group-id "$SECURITY_GROUP" \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0

    echo "✅ Created security group: $SECURITY_GROUP"
fi

# Create user data script for instance initialization
cat > /tmp/ninaivalaigal-userdata.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y curl jq git make postgresql-client

# Install Apple Container CLI (simulated with Podman for cloud compatibility)
apt-get install -y podman
ln -sf /usr/bin/podman /usr/local/bin/container

# Create ninaivalaigal user
useradd -m -s /bin/bash ninaivalaigal
usermod -aG sudo ninaivalaigal

# Clone ninaivalaigal repository
cd /home/ninaivalaigal
git clone https://github.com/Arunosaur/ninaivalaigal.git
chown -R ninaivalaigal:ninaivalaigal ninaivalaigal

# Setup systemd service for ninaivalaigal
cat > /etc/systemd/system/ninaivalaigal.service << 'SERVICE'
[Unit]
Description=Ninaivalaigal Stack
After=network.target

[Service]
Type=forking
User=ninaivalaigal
WorkingDirectory=/home/ninaivalaigal/ninaivalaigal
ExecStart=/usr/bin/make dev-up
ExecStop=/usr/bin/make dev-down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
systemctl daemon-reload
systemctl enable ninaivalaigal
systemctl start ninaivalaigal

# Setup log rotation
cat > /etc/logrotate.d/ninaivalaigal << 'LOGROTATE'
/var/log/ninaivalaigal/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
LOGROTATE

echo "✅ Ninaivalaigal setup complete"
EOF

echo "🚀 Launching EC2 instance..."

# Launch EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
    --region "$AWS_REGION" \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SECURITY_GROUP" \
    ${SUBNET_ID:+--subnet-id "$SUBNET_ID"} \
    --user-data file:///tmp/ninaivalaigal-userdata.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo ""
echo "⏳ Waiting for instance to be running..."

# Wait for instance to be running
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

# Get instance details
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0]')

PUBLIC_IP=$(echo "$INSTANCE_INFO" | jq -r '.PublicIpAddress')
PRIVATE_IP=$(echo "$INSTANCE_INFO" | jq -r '.PrivateIpAddress')

echo "✅ Instance is running!"
echo ""
echo "📋 Instance Details:"
echo "   Instance ID: $INSTANCE_ID"
echo "   Public IP:   $PUBLIC_IP"
echo "   Private IP:  $PRIVATE_IP"
echo "   Region:      $AWS_REGION"
echo ""
echo "🌍 Access URLs (available in ~2-3 minutes):"
echo "   API Health:  http://$PUBLIC_IP:8080/health"
echo "   API Docs:    http://$PUBLIC_IP:8080/docs"
echo "   API Metrics: http://$PUBLIC_IP:8080/metrics"
echo ""
echo "🔐 SSH Access:"
echo "   ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "📊 Monitor deployment:"
echo "   ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP 'sudo journalctl -u ninaivalaigal -f'"
echo ""
echo "🛑 To terminate instance:"
echo "   aws ec2 terminate-instances --region $AWS_REGION --instance-ids $INSTANCE_ID"

# Clean up temporary files
rm -f /tmp/ninaivalaigal-userdata.sh

echo ""
echo "✨ AWS deployment complete! Instance is initializing ninaivalaigal stack."
