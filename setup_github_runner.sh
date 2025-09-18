#!/bin/bash
set -e

echo "🏃 GitHub Actions Runner Setup for Mac Studio"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as correct user
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Get repository URL and token
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <REPO_URL> <RUNNER_TOKEN>"
    echo ""
    echo "Example:"
    echo "  $0 https://github.com/Arunosaur/ninaivalaigal ghp_xxxxxxxxxxxxxxxxxxxx"
    echo ""
    echo "To get a runner token:"
    echo "1. Go to your GitHub repo"
    echo "2. Settings > Actions > Runners"
    echo "3. Click 'New self-hosted runner'"
    echo "4. Select macOS ARM64"
    echo "5. Copy the token from the configuration command"
    exit 1
fi

REPO_URL="$1"
RUNNER_TOKEN="$2"

# Validate inputs
if [[ ! "$REPO_URL" =~ ^https://github\.com/.+/.+$ ]]; then
    log_error "Invalid repository URL format. Expected: https://github.com/owner/repo"
    exit 1
fi

if [[ ! "$RUNNER_TOKEN" =~ ^[A-Z0-9]{29}$ ]]; then
    log_error "Invalid runner token format. Expected: 29 character alphanumeric string"
    exit 1
fi

log_step "Setting up GitHub Actions runner for: $REPO_URL"

# 1. Create runner directory
RUNNER_DIR="/opt/actions-runner"
log_step "Creating runner directory..."
sudo mkdir -p "$RUNNER_DIR"
sudo chown -R $(whoami) "$RUNNER_DIR"
log_success "Runner directory created: $RUNNER_DIR"

# 2. Download latest runner
log_step "Downloading GitHub Actions runner..."
cd "$RUNNER_DIR"

# Get latest release info
LATEST_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' | sed 's/v//')
RUNNER_URL="https://github.com/actions/runner/releases/download/v${LATEST_VERSION}/actions-runner-osx-arm64-${LATEST_VERSION}.tar.gz"

log_step "Downloading runner version $LATEST_VERSION..."
curl -o actions-runner.tar.gz -L "$RUNNER_URL"

# Verify download
if [ ! -f "actions-runner.tar.gz" ]; then
    log_error "Failed to download runner"
    exit 1
fi

log_success "Runner downloaded successfully"

# 3. Extract runner
log_step "Extracting runner..."
tar xzf actions-runner.tar.gz
rm actions-runner.tar.gz
log_success "Runner extracted"

# 4. Configure runner
log_step "Configuring runner..."

# Generate unique runner name
RUNNER_NAME="mac-studio-$(hostname -s)-$(date +%s)"

./config.sh \
    --url "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --name "$RUNNER_NAME" \
    --labels "macstudio,arm64,self-hosted,macos" \
    --work "_work" \
    --replace \
    --unattended

log_success "Runner configured with name: $RUNNER_NAME"

# 5. Install as service
log_step "Installing runner as system service..."
sudo ./svc.sh install

# 6. Start service
log_step "Starting runner service..."
sudo ./svc.sh start

# 7. Verify service status
log_step "Verifying service status..."
sleep 5

if sudo ./svc.sh status | grep -q "active"; then
    log_success "Runner service is active and running"
else
    log_warning "Runner service status unclear - check manually"
fi

# 8. Display configuration
echo ""
echo "=============================================="
log_success "GitHub Actions Runner Setup Complete!"
echo "=============================================="
echo ""
echo "📊 Configuration Summary:"
echo "  Repository: $REPO_URL"
echo "  Runner Name: $RUNNER_NAME"
echo "  Labels: macstudio, arm64, self-hosted, macos"
echo "  Installation: $RUNNER_DIR"
echo ""
echo "🔧 Management Commands:"
echo "  Check status: sudo $RUNNER_DIR/svc.sh status"
echo "  Stop service: sudo $RUNNER_DIR/svc.sh stop"
echo "  Start service: sudo $RUNNER_DIR/svc.sh start"
echo "  Restart service: sudo $RUNNER_DIR/svc.sh stop && sudo $RUNNER_DIR/svc.sh start"
echo "  View logs: tail -f $RUNNER_DIR/_diag/Runner_*.log"
echo ""
echo "🎯 Next Steps:"
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings > Actions > Runners"
echo "3. Verify your runner appears as 'Online'"
echo "4. Update your workflow files to use: runs-on: [self-hosted, macstudio]"
echo ""
echo "⚡ Performance Benefits:"
echo "- 20-core M2 Ultra for parallel testing"
echo "- 128GB RAM for large datasets"
echo "- Native ARM64 performance"
echo "- Always-on dedicated runner"
echo ""

# 9. Test runner connectivity
log_step "Testing runner connectivity..."
if curl -s "https://api.github.com/repos/${REPO_URL#https://github.com/}/actions/runners" | grep -q "$RUNNER_NAME"; then
    log_success "Runner successfully registered with GitHub"
else
    log_warning "Unable to verify runner registration - check GitHub repo settings"
fi

echo "🎉 Setup complete! Your Mac Studio is now ready for blazing fast CI/CD!"
