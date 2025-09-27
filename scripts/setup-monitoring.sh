#!/bin/bash
set -euo pipefail

# Foundation Test Monitoring Setup Script
# Sets up Slack and HealthChecks.io integration for Foundation test monitoring

echo "🚨 Foundation Test Monitoring Setup"
echo "=================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to check if GitHub CLI is available
check_gh_cli() {
    if command -v gh >/dev/null 2>&1; then
        print_status "SUCCESS" "GitHub CLI is available"
        return 0
    else
        print_status "ERROR" "GitHub CLI not found. Install with: brew install gh"
        return 1
    fi
}

# Function to check if user is authenticated with GitHub
check_gh_auth() {
    if gh auth status >/dev/null 2>&1; then
        print_status "SUCCESS" "GitHub CLI is authenticated"
        return 0
    else
        print_status "ERROR" "GitHub CLI not authenticated. Run: gh auth login"
        return 1
    fi
}

# Function to set GitHub secret
set_github_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        print_status "WARNING" "Skipping $secret_name (empty value)"
        return 0
    fi
    
    if gh secret set "$secret_name" --body "$secret_value" >/dev/null 2>&1; then
        print_status "SUCCESS" "Set GitHub secret: $secret_name"
        return 0
    else
        print_status "ERROR" "Failed to set GitHub secret: $secret_name"
        return 1
    fi
}

# Function to create local environment file
create_local_env() {
    local env_file=".env.monitoring"
    
    cat > "$env_file" << 'EOF'
# Foundation Test Monitoring Configuration
# Copy this file to .env and fill in your actual values

# Slack Integration (Optional)
# Get webhook URL from: https://api.slack.com/apps -> Incoming Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# HealthChecks.io Integration (Optional)  
# Get UUID from: https://healthchecks.io/ -> Create Check -> Copy UUID
HEALTHCHECK_UUID=your-healthchecks-io-uuid-here

# Local Testing Environment
POSTGRES_PASSWORD=foundation_test_password_123
REDIS_PASSWORD=foundation_redis_456
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/foundation_test
REDIS_URL=redis://localhost:6379/15
EOF

    print_status "SUCCESS" "Created $env_file template"
    print_status "INFO" "Edit $env_file with your actual webhook URLs and UUIDs"
}

# Function to load environment variables
load_env() {
    local env_file=".env.monitoring"
    
    if [ -f "$env_file" ]; then
        # Source the file to load variables
        set -a
        source "$env_file"
        set +a
        print_status "SUCCESS" "Loaded environment from $env_file"
        return 0
    else
        print_status "WARNING" "No $env_file found. Using environment variables or prompting."
        return 1
    fi
}

# Function to prompt for monitoring configuration
prompt_for_config() {
    print_status "INFO" "Setting up monitoring integration..."
    
    # Slack configuration
    echo ""
    echo "📱 Slack Integration Setup:"
    echo "1. Go to https://api.slack.com/apps"
    echo "2. Create a new app or select existing app"
    echo "3. Go to 'Incoming Webhooks' and create webhook"
    echo "4. Copy the webhook URL"
    echo ""
    
    if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
        read -p "Enter Slack Webhook URL (or press Enter to skip): " SLACK_WEBHOOK_URL
    fi
    
    # HealthChecks.io configuration
    echo ""
    echo "🏥 HealthChecks.io Integration Setup:"
    echo "1. Go to https://healthchecks.io/"
    echo "2. Create account and new check named 'Foundation SPEC Tests'"
    echo "3. Set schedule to 'Daily'"
    echo "4. Copy the check UUID from the URL"
    echo ""
    
    if [ -z "${HEALTHCHECK_UUID:-}" ]; then
        read -p "Enter HealthChecks.io UUID (or press Enter to skip): " HEALTHCHECK_UUID
    fi
}

# Function to validate monitoring setup
validate_monitoring() {
    local validation_passed=true
    
    print_status "INFO" "Validating monitoring setup..."
    
    # Test Slack webhook if provided
    if [ -n "${SLACK_WEBHOOK_URL:-}" ] && [ "$SLACK_WEBHOOK_URL" != "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" ]; then
        print_status "INFO" "Testing Slack webhook..."
        
        local test_payload='{"text":"🧪 Foundation Test Monitoring Setup - Test Message"}'
        
        if curl -s -X POST -H 'Content-type: application/json' --data "$test_payload" "$SLACK_WEBHOOK_URL" >/dev/null; then
            print_status "SUCCESS" "Slack webhook test successful"
        else
            print_status "ERROR" "Slack webhook test failed"
            validation_passed=false
        fi
    else
        print_status "INFO" "Slack webhook not configured (optional)"
    fi
    
    # Test HealthChecks.io if provided
    if [ -n "${HEALTHCHECK_UUID:-}" ] && [ "$HEALTHCHECK_UUID" != "your-healthchecks-io-uuid-here" ]; then
        print_status "INFO" "Testing HealthChecks.io ping..."
        
        if curl -fsS -m 10 --retry 3 -o /dev/null "https://hc-ping.com/$HEALTHCHECK_UUID" 2>/dev/null; then
            print_status "SUCCESS" "HealthChecks.io ping test successful"
        else
            print_status "ERROR" "HealthChecks.io ping test failed"
            validation_passed=false
        fi
    else
        print_status "INFO" "HealthChecks.io not configured (optional)"
    fi
    
    return $([ "$validation_passed" = true ] && echo 0 || echo 1)
}

# Function to set up GitHub secrets
setup_github_secrets() {
    print_status "INFO" "Setting up GitHub repository secrets..."
    
    # Check GitHub CLI availability and authentication
    if ! check_gh_cli || ! check_gh_auth; then
        print_status "ERROR" "Cannot set GitHub secrets without GitHub CLI"
        return 1
    fi
    
    # Set secrets if provided
    local secrets_set=0
    
    if [ -n "${SLACK_WEBHOOK_URL:-}" ] && [ "$SLACK_WEBHOOK_URL" != "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" ]; then
        if set_github_secret "SLACK_WEBHOOK_URL" "$SLACK_WEBHOOK_URL"; then
            ((secrets_set++))
        fi
    fi
    
    if [ -n "${HEALTHCHECK_UUID:-}" ] && [ "$HEALTHCHECK_UUID" != "your-healthchecks-io-uuid-here" ]; then
        if set_github_secret "HEALTHCHECK_UUID" "$HEALTHCHECK_UUID"; then
            ((secrets_set++))
        fi
    fi
    
    print_status "SUCCESS" "Set $secrets_set GitHub secrets"
    
    if [ $secrets_set -eq 0 ]; then
        print_status "WARNING" "No monitoring secrets configured. Foundation tests will run without external notifications."
    fi
}

# Function to create monitoring test script
create_monitoring_test() {
    cat > "test-monitoring.sh" << 'EOF'
#!/bin/bash
# Test monitoring integration

echo "🧪 Testing Foundation Test Monitoring..."

# Load environment
if [ -f ".env.monitoring" ]; then
    set -a
    source .env.monitoring
    set +a
fi

# Test Slack notification
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "📱 Testing Slack notification..."
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🧪 Foundation Test Monitoring - Manual Test"}' \
        "$SLACK_WEBHOOK_URL"
    echo "✅ Slack test sent"
fi

# Test HealthChecks.io ping
if [ -n "${HEALTHCHECK_UUID:-}" ]; then
    echo "🏥 Testing HealthChecks.io ping..."
    curl -fsS -m 10 --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID"
    echo "✅ HealthChecks.io ping sent"
fi

echo "🎉 Monitoring test complete!"
EOF

    chmod +x test-monitoring.sh
    print_status "SUCCESS" "Created test-monitoring.sh script"
}

# Main execution
main() {
    echo ""
    print_status "INFO" "Starting Foundation Test Monitoring setup..."
    
    # Create local environment template
    create_local_env
    
    # Try to load existing environment
    load_env || true
    
    # Prompt for configuration if not already set
    prompt_for_config
    
    # Validate monitoring setup
    if validate_monitoring; then
        print_status "SUCCESS" "Monitoring validation passed"
    else
        print_status "WARNING" "Some monitoring tests failed (non-blocking)"
    fi
    
    # Set up GitHub secrets
    setup_github_secrets
    
    # Create monitoring test script
    create_monitoring_test
    
    echo ""
    print_status "SUCCESS" "Foundation Test Monitoring setup complete!"
    echo ""
    print_status "INFO" "Next steps:"
    echo "  1. Edit .env.monitoring with your actual webhook URLs"
    echo "  2. Run ./test-monitoring.sh to test integration"
    echo "  3. Run make test-foundation to trigger monitored tests"
    echo "  4. Check Slack/HealthChecks.io for notifications"
    echo ""
    print_status "INFO" "GitHub Actions will now send notifications on Foundation test failures"
}

# Run main function
main "$@"
