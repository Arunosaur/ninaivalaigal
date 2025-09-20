#!/bin/bash
set -euo pipefail

# Azure deployment script for ninaivalaigal Apple Container CLI stack
# Deploys to Azure Container Instances or Azure VM

RESOURCE_GROUP="${RESOURCE_GROUP:-}"
LOCATION="${LOCATION:-eastus}"
VM_SIZE="${VM_SIZE:-Standard_B2s}"
VM_NAME="${VM_NAME:-ninaivalaigal-vm}"
ADMIN_USERNAME="${ADMIN_USERNAME:-azureuser}"
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/id_rsa.pub}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-vm}"  # vm or aci

echo "🚀 Deploying ninaivalaigal to Microsoft Azure"
echo "============================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Deployment Type: $DEPLOYMENT_TYPE"
echo "VM Size: $VM_SIZE"
echo ""

# Check Azure CLI
if ! command -v az >/dev/null 2>&1; then
    echo "❌ Azure CLI not found. Please install it first:"
    echo "   brew install azure-cli"
    exit 1
fi

# Check Azure authentication
if ! az account show >/dev/null 2>&1; then
    echo "❌ Not authenticated with Azure. Please run:"
    echo "   az login"
    exit 1
fi

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    echo "❌ Error: RESOURCE_GROUP is required"
    echo ""
    echo "Usage: RESOURCE_GROUP=my-rg ./scripts/deploy-azure.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  LOCATION        - Azure region (default: eastus)"
    echo "  VM_SIZE         - VM size (default: Standard_B2s)"
    echo "  VM_NAME         - VM name (default: ninaivalaigal-vm)"
    echo "  ADMIN_USERNAME  - Admin username (default: azureuser)"
    echo "  SSH_KEY_PATH    - SSH public key path (default: ~/.ssh/id_rsa.pub)"
    echo "  DEPLOYMENT_TYPE - vm|aci (default: vm)"
    exit 1
fi

# Create resource group if it doesn't exist
echo "🔧 Setting up Azure resources..."
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo "📦 Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
else
    echo "✅ Resource group exists: $RESOURCE_GROUP"
fi

case "$DEPLOYMENT_TYPE" in
    "vm")
        echo "🖥️  Deploying to Azure Virtual Machine..."

        # Check SSH key
        if [ ! -f "$SSH_KEY_PATH" ]; then
            echo "❌ SSH public key not found at: $SSH_KEY_PATH"
            echo "   Generate one with: ssh-keygen -t rsa -b 4096"
            exit 1
        fi

        # Create Network Security Group
        echo "🔒 Creating Network Security Group..."
        NSG_NAME="${VM_NAME}-nsg"
        az network nsg create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$NSG_NAME" \
            --location "$LOCATION"

        # Add security rules
        az network nsg rule create \
            --resource-group "$RESOURCE_GROUP" \
            --nsg-name "$NSG_NAME" \
            --name "SSH" \
            --protocol tcp \
            --priority 1001 \
            --destination-port-range 22 \
            --access allow

        az network nsg rule create \
            --resource-group "$RESOURCE_GROUP" \
            --nsg-name "$NSG_NAME" \
            --name "HTTP" \
            --protocol tcp \
            --priority 1002 \
            --destination-port-range 8080 \
            --access allow

        # Create cloud-init script
        cat > /tmp/ninaivalaigal-cloud-init.yml << 'EOF'
#cloud-config
package_upgrade: true
packages:
  - curl
  - jq
  - git
  - make
  - postgresql-client

runcmd:
  # Install Podman (Apple Container CLI alternative)
  - apt-get update
  - apt-get install -y podman
  - ln -sf /usr/bin/podman /usr/local/bin/container

  # Create ninaivalaigal user
  - useradd -m -s /bin/bash ninaivalaigal
  - usermod -aG sudo ninaivalaigal

  # Clone ninaivalaigal repository
  - cd /home/ninaivalaigal
  - sudo -u ninaivalaigal git clone https://github.com/Arunosaur/ninaivalaigal.git

  # Setup systemd service
  - |
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
  - systemctl daemon-reload
  - systemctl enable ninaivalaigal
  - systemctl start ninaivalaigal

  # Setup nginx reverse proxy
  - apt-get install -y nginx
  - |
    cat > /etc/nginx/sites-available/ninaivalaigal << 'NGINX'
    server {
        listen 8080;
        server_name _;

        location / {
            proxy_pass http://localhost:13370;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    NGINX

  - ln -sf /etc/nginx/sites-available/ninaivalaigal /etc/nginx/sites-enabled/
  - rm -f /etc/nginx/sites-enabled/default
  - systemctl restart nginx
  - systemctl enable nginx

write_files:
  - path: /var/log/ninaivalaigal-setup.log
    content: |
      Ninaivalaigal Azure VM setup started
    permissions: '0644'
EOF

        echo "🚀 Creating Azure VM..."

        # Create VM
        az vm create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$VM_NAME" \
            --image "Ubuntu2204" \
            --size "$VM_SIZE" \
            --admin-username "$ADMIN_USERNAME" \
            --ssh-key-values "$SSH_KEY_PATH" \
            --nsg "$NSG_NAME" \
            --custom-data /tmp/ninaivalaigal-cloud-init.yml \
            --location "$LOCATION"

        # Get VM details
        VM_INFO=$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --show-details)
        PUBLIC_IP=$(echo "$VM_INFO" | jq -r '.publicIps')
        PRIVATE_IP=$(echo "$VM_INFO" | jq -r '.privateIps')

        echo "✅ VM created successfully!"
        echo ""
        echo "📋 VM Details:"
        echo "   VM Name:     $VM_NAME"
        echo "   Public IP:   $PUBLIC_IP"
        echo "   Private IP:  $PRIVATE_IP"
        echo "   Location:    $LOCATION"
        echo "   Size:        $VM_SIZE"
        echo ""
        echo "🌍 Access URLs (available in ~3-5 minutes):"
        echo "   API Health:  http://$PUBLIC_IP:8080/health"
        echo "   API Docs:    http://$PUBLIC_IP:8080/docs"
        echo "   API Metrics: http://$PUBLIC_IP:8080/metrics"
        echo ""
        echo "🔐 SSH Access:"
        echo "   ssh $ADMIN_USERNAME@$PUBLIC_IP"
        echo ""
        echo "📊 Monitor deployment:"
        echo "   ssh $ADMIN_USERNAME@$PUBLIC_IP 'sudo journalctl -u ninaivalaigal -f'"
        echo ""
        echo "🛑 To delete resources:"
        echo "   az group delete --name $RESOURCE_GROUP --yes --no-wait"

        # Clean up temporary files
        rm -f /tmp/ninaivalaigal-cloud-init.yml
        ;;

    "aci")
        echo "📦 Deploying to Azure Container Instances..."

        # Create container group with ninaivalaigal stack
        echo "🚀 Creating container group..."

        # Note: ACI doesn't support privileged containers needed for Apple Container CLI
        # This is a simplified deployment using standard containers
        az container create \
            --resource-group "$RESOURCE_GROUP" \
            --name "ninaivalaigal-aci" \
            --image "postgres:15" \
            --dns-name-label "ninaivalaigal-${RANDOM}" \
            --ports 5432 \
            --environment-variables \
                POSTGRES_DB=nina \
                POSTGRES_USER=nina \
                POSTGRES_PASSWORD=change_me_securely \
            --location "$LOCATION"

        # Get container details
        CONTAINER_INFO=$(az container show --resource-group "$RESOURCE_GROUP" --name "ninaivalaigal-aci")
        FQDN=$(echo "$CONTAINER_INFO" | jq -r '.ipAddress.fqdn')

        echo "✅ Container group created!"
        echo ""
        echo "📋 Container Details:"
        echo "   Container Name: ninaivalaigal-aci"
        echo "   FQDN:          $FQDN"
        echo "   Location:      $LOCATION"
        echo ""
        echo "⚠️  Note: ACI deployment is simplified (PostgreSQL only)"
        echo "   For full stack, use VM deployment: DEPLOYMENT_TYPE=vm"
        echo ""
        echo "🔗 Database Connection:"
        echo "   postgresql://nina:change_me_securely@$FQDN:5432/nina"  # pragma: allowlist secret
        echo ""
        echo "🛑 To delete container:"
        echo "   az container delete --resource-group $RESOURCE_GROUP --name ninaivalaigal-aci --yes"
        ;;

    *)
        echo "❌ Unknown deployment type: $DEPLOYMENT_TYPE"
        echo "   Supported types: vm, aci"
        exit 1
        ;;
esac

echo ""
echo "✨ Azure deployment complete! Your ninaivalaigal stack is being initialized."
