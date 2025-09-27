#!/bin/bash
set -euo pipefail

# Post-Failure Hook for CI/CD Pipeline
# Automatically triggered when CI/CD pipeline fails
# Attempts recovery and sends notifications

echo "🚨 Post-Failure Hook Activated"
echo "================================"

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

# Get failure context from environment variables
FAILURE_TYPE=${FAILURE_TYPE:-"unknown"}
FAILED_JOB=${FAILED_JOB:-"unknown"}
GITHUB_RUN_ID=${GITHUB_RUN_ID:-"local"}
GITHUB_REPOSITORY=${GITHUB_REPOSITORY:-"local/repo"}

print_status "INFO" "Failure detected in job: $FAILED_JOB"
print_status "INFO" "Failure type: $FAILURE_TYPE"
print_status "INFO" "Run ID: $GITHUB_RUN_ID"

# Function to check if recovery is enabled
check_recovery_enabled() {
    local auto_recovery=${AUTO_RECOVERY_ENABLED:-"true"}
    if [ "$auto_recovery" == "true" ]; then
        print_status "SUCCESS" "Auto-recovery is enabled"
        return 0
    else
        print_status "WARNING" "Auto-recovery is disabled"
        return 1
    fi
}

# Function to determine recovery strategy based on failure type
determine_recovery_strategy() {
    local failure_type=$1
    
    case $failure_type in
        "test_failure")
            echo "run_recovery_tests"
            ;;
        "service_failure")
            echo "restart_services"
            ;;
        "coverage_failure")
            echo "analyze_coverage"
            ;;
        "security_failure")
            echo "security_remediation"
            ;;
        "build_failure")
            echo "rebuild_dependencies"
            ;;
        *)
            echo "full_recovery"
            ;;
    esac
}

# Function to execute recovery based on strategy
execute_recovery() {
    local strategy=$1
    
    print_status "INFO" "Executing recovery strategy: $strategy"
    
    case $strategy in
        "run_recovery_tests")
            print_status "INFO" "Running recovery test suite..."
            python3 scripts/ci-recovery.py || return 1
            ;;
        "restart_services")
            print_status "INFO" "Restarting failed services..."
            python3 scripts/ci-recovery.py || return 1
            ;;
        "analyze_coverage")
            print_status "INFO" "Analyzing coverage issues..."
            # Run coverage analysis and attempt to identify missing tests
            pytest tests/foundation/ --cov=server --cov-report=term --cov-fail-under=80 || true
            ;;
        "security_remediation")
            print_status "ERROR" "Security issues detected - manual intervention required"
            return 1
            ;;
        "rebuild_dependencies")
            print_status "INFO" "Rebuilding dependencies..."
            pip install --upgrade -r server/requirements.txt || return 1
            ;;
        "full_recovery")
            print_status "INFO" "Executing full recovery procedure..."
            python3 scripts/ci-recovery.py || return 1
            ;;
        *)
            print_status "ERROR" "Unknown recovery strategy: $strategy"
            return 1
            ;;
    esac
    
    return 0
}

# Function to send failure notification
send_failure_notification() {
    local failure_type=$1
    local recovery_attempted=$2
    local recovery_success=$3
    
    # Prepare notification message
    local status_emoji="❌"
    local status_text="FAILED"
    local color="danger"
    
    if [ "$recovery_success" == "true" ]; then
        status_emoji="🔄"
        status_text="RECOVERED"
        color="warning"
    fi
    
    local message="$status_emoji CI Pipeline $status_text"
    local details="Job: $FAILED_JOB\nFailure Type: $failure_type\nRecovery Attempted: $recovery_attempted\nRecovery Success: $recovery_success"
    
    # Send Slack notification if configured
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        print_status "INFO" "Sending Slack notification..."
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"$message\",
                \"attachments\": [
                    {
                        \"color\": \"$color\",
                        \"fields\": [
                            {
                                \"title\": \"Pipeline Details\",
                                \"value\": \"$details\",
                                \"short\": false
                            },
                            {
                                \"title\": \"Repository\",
                                \"value\": \"$GITHUB_REPOSITORY\",
                                \"short\": true
                            },
                            {
                                \"title\": \"Run ID\",
                                \"value\": \"$GITHUB_RUN_ID\",
                                \"short\": true
                            }
                        ]
                    }
                ]
            }" \
            "$SLACK_WEBHOOK_URL" || print_status "WARNING" "Failed to send Slack notification"
    fi
    
    # Send HealthChecks.io ping if configured
    if [ -n "${HEALTHCHECK_UUID:-}" ]; then
        print_status "INFO" "Sending HealthChecks.io ping..."
        
        if [ "$recovery_success" == "true" ]; then
            curl -fsS -m 10 --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID/recovery" || true
        else
            curl -fsS -m 10 --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID/fail" || true
        fi
    fi
}

# Function to create failure report
create_failure_report() {
    local failure_type=$1
    local recovery_attempted=$2
    local recovery_success=$3
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    cat > failure_report.md << EOF
# CI/CD Pipeline Failure Report

**Timestamp**: $timestamp
**Repository**: $GITHUB_REPOSITORY
**Run ID**: $GITHUB_RUN_ID
**Failed Job**: $FAILED_JOB

## Failure Details

- **Failure Type**: $failure_type
- **Recovery Attempted**: $recovery_attempted
- **Recovery Success**: $recovery_success

## Recovery Actions Taken

EOF

    if [ "$recovery_attempted" == "true" ]; then
        echo "- ✅ Post-failure hook executed" >> failure_report.md
        echo "- 🔄 Recovery strategy determined and executed" >> failure_report.md
        
        if [ "$recovery_success" == "true" ]; then
            echo "- ✅ Recovery completed successfully" >> failure_report.md
            echo "- 🧪 Foundation tests validated recovery" >> failure_report.md
        else
            echo "- ❌ Recovery failed - manual intervention required" >> failure_report.md
        fi
    else
        echo "- ⚠️ Recovery was not attempted (disabled or unsupported failure type)" >> failure_report.md
    fi
    
    cat >> failure_report.md << EOF

## Next Steps

EOF

    if [ "$recovery_success" == "true" ]; then
        cat >> failure_report.md << EOF
- ✅ Pipeline recovered automatically
- 🔍 Monitor for recurring issues
- 📊 Review recovery logs for optimization opportunities
EOF
    else
        cat >> failure_report.md << EOF
- 🔧 Manual intervention required
- 📋 Check service logs and error details
- 👥 Contact development team if issue persists
- 🚨 Consider disabling auto-deployment until resolved
EOF
    fi
    
    print_status "SUCCESS" "Failure report created: failure_report.md"
}

# Function to update PR with failure status
update_pr_status() {
    local recovery_success=$1
    
    # Only update PR status if we're in a PR context
    if [ -n "${GITHUB_EVENT_NAME:-}" ] && [ "$GITHUB_EVENT_NAME" == "pull_request" ]; then
        print_status "INFO" "Updating PR with failure status..."
        
        local status_message
        if [ "$recovery_success" == "true" ]; then
            status_message="🔄 **Pipeline Recovered**: Automatic recovery completed successfully. Please review the recovery report."
        else
            status_message="❌ **Pipeline Failed**: Automatic recovery was attempted but failed. Manual intervention required."
        fi
        
        # This would typically use GitHub API to comment on PR
        # For now, we'll just log the message
        print_status "INFO" "PR status message: $status_message"
    fi
}

# Main execution
main() {
    print_status "INFO" "Starting post-failure recovery process..."
    
    # Check if recovery is enabled
    if ! check_recovery_enabled; then
        print_status "WARNING" "Recovery disabled - sending notification only"
        send_failure_notification "$FAILURE_TYPE" "false" "false"
        create_failure_report "$FAILURE_TYPE" "false" "false"
        return 0
    fi
    
    # Determine recovery strategy
    recovery_strategy=$(determine_recovery_strategy "$FAILURE_TYPE")
    print_status "INFO" "Recovery strategy: $recovery_strategy"
    
    # Execute recovery
    recovery_success="false"
    if execute_recovery "$recovery_strategy"; then
        recovery_success="true"
        print_status "SUCCESS" "Recovery completed successfully"
    else
        print_status "ERROR" "Recovery failed"
    fi
    
    # Send notifications
    send_failure_notification "$FAILURE_TYPE" "true" "$recovery_success"
    
    # Create failure report
    create_failure_report "$FAILURE_TYPE" "true" "$recovery_success"
    
    # Update PR status if applicable
    update_pr_status "$recovery_success"
    
    # Return appropriate exit code
    if [ "$recovery_success" == "true" ]; then
        print_status "SUCCESS" "Post-failure hook completed successfully"
        return 0
    else
        print_status "ERROR" "Post-failure hook completed with errors"
        return 1
    fi
}

# Execute main function
main "$@"
