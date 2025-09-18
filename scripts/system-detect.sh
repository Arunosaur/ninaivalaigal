#!/usr/bin/env bash
# System detection and environment validation
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log(){ printf "${CYAN}[system]${NC} %s\n" "$*"; }
warn(){ printf "${YELLOW}[warn]${NC} %s\n" "$*"; }
error(){ printf "${RED}[error]${NC} %s\n" "$*"; }
success(){ printf "${GREEN}[success]${NC} %s\n" "$*"; }

detect_system(){
    local system_info=""
    
    # Check if we're in a deployment environment (skip interactive prompts)
    local is_deployment=false
    if [[ -n "${CI:-}" ]] || [[ -n "${GITHUB_ACTIONS:-}" ]] || [[ -n "${DEPLOYMENT_ENV:-}" ]] || [[ -n "${DOCKER_CONTAINER:-}" ]] || [[ -f "/.dockerenv" ]]; then
        is_deployment=true
    fi
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local macos_version=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
        system_info="macOS $macos_version"
        
        # Detect Mac model (only if not in deployment)
        if [[ "$is_deployment" == false ]]; then
            local model=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Model Name" | cut -d: -f2 | xargs || echo "unknown")
            local chip=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Chip" | cut -d: -f2 | xargs || echo "unknown")
            local memory=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Memory" | cut -d: -f2 | xargs || echo "unknown")
        else
            local model="deployment"
            local chip="deployment"
            local memory="deployment"
        fi
        
        echo "SYSTEM_OS=macOS"
        echo "SYSTEM_VERSION=$macos_version"
        echo "SYSTEM_MODEL=$model"
        echo "SYSTEM_CHIP=$chip"
        echo "SYSTEM_MEMORY=$memory"
        echo "SYSTEM_IS_DEPLOYMENT=$is_deployment"
        
        # Determine role based on deployment context
        if [[ "$is_deployment" == true ]]; then
            echo "SYSTEM_ROLE=deployment"
            echo "SYSTEM_CAPABILITIES=production_stack,ci_runner,automated_testing"
        elif [[ "$model" == *"Mac Studio"* ]] || [[ "$chip" == *"M1 Ultra"* ]] || [[ "$memory" == *"128 GB"* ]]; then
            echo "SYSTEM_ROLE=studio"
            echo "SYSTEM_CAPABILITIES=heavy_validation,ci_runner,production_stack"
        else
            echo "SYSTEM_ROLE=laptop"
            echo "SYSTEM_CAPABILITIES=development,authoring,hot_reload"
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Detect Linux environment type
        local distro="unknown"
        if [[ -f "/etc/os-release" ]]; then
            distro=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"' || echo "unknown")
        fi
        
        # Check if we're in a container
        local container_type="none"
        if [[ -f "/.dockerenv" ]]; then
            container_type="docker"
        elif [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
            container_type="kubernetes"
        elif [[ -n "${CONTAINER:-}" ]]; then
            container_type="generic"
        fi
        
        system_info="Linux ($distro)"
        if [[ "$container_type" != "none" ]]; then
            system_info="$system_info in $container_type"
        fi
        
        echo "SYSTEM_OS=linux"
        echo "SYSTEM_VERSION=$distro"
        echo "SYSTEM_MODEL=server"
        echo "SYSTEM_CHIP=unknown"
        echo "SYSTEM_MEMORY=unknown"
        echo "SYSTEM_IS_DEPLOYMENT=$is_deployment"
        echo "SYSTEM_CONTAINER_TYPE=$container_type"
        
        # Role determination for Linux
        if [[ "$is_deployment" == true ]] || [[ "$container_type" != "none" ]]; then
            echo "SYSTEM_ROLE=deployment"
            echo "SYSTEM_CAPABILITIES=production_stack,ci_runner,automated_testing"
        else
            echo "SYSTEM_ROLE=server"
            echo "SYSTEM_CAPABILITIES=ci_runner,production_stack,development"
        fi
        
    else
        system_info="Unknown OS ($OSTYPE)"
        echo "SYSTEM_OS=unknown"
        echo "SYSTEM_VERSION=unknown"
        echo "SYSTEM_MODEL=unknown"
        echo "SYSTEM_CHIP=unknown"
        echo "SYSTEM_MEMORY=unknown"
        echo "SYSTEM_IS_DEPLOYMENT=$is_deployment"
        echo "SYSTEM_ROLE=unknown"
        echo "SYSTEM_CAPABILITIES=basic"
    fi
    
    log "Detected: $system_info"
}

check_container_runtime(){
    if command -v container >/dev/null 2>&1; then
        local version=$(container --version 2>/dev/null || echo "unknown")
        success "Apple Container CLI: $version"
        echo "CONTAINER_RUNTIME=apple"
        echo "CONTAINER_VERSION=$version"
        return 0
    elif command -v docker >/dev/null 2>&1; then
        local version=$(docker --version 2>/dev/null || echo "unknown")
        warn "Docker detected: $version (Apple Container CLI preferred)"
        echo "CONTAINER_RUNTIME=docker"
        echo "CONTAINER_VERSION=$version"
        return 0
    else
        error "No container runtime found"
        echo "CONTAINER_RUNTIME=none"
        return 1
    fi
}

check_development_tools(){
    local tools=("git" "make" "curl" "python3" "node" "npm")
    local missing=()
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            local version=$($tool --version 2>/dev/null | head -n1 || echo "unknown")
            local tool_upper=$(echo "$tool" | tr '[:lower:]' '[:upper:]')
            echo "TOOL_${tool_upper}=available"
        else
            missing+=("$tool")
            local tool_upper=$(echo "$tool" | tr '[:lower:]' '[:upper:]')
            echo "TOOL_${tool_upper}=missing"
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Missing tools: ${missing[*]}"
        echo "MISSING_TOOLS=${missing[*]}"
    else
        success "All development tools available"
        echo "MISSING_TOOLS="
    fi
}

recommend_actions(){
    local system_role="${1:-unknown}"
    local is_deployment="${2:-false}"
    
    log "Recommendations for $system_role:"
    
    case "$system_role" in
        "deployment")
            echo "  • Deployment environment detected - automated operations enabled"
            echo "  • Interactive prompts disabled for CI/CD compatibility"
            echo "  • Optimized for: automated testing, production deployments"
            ;;
        "studio")
            echo "  • Perfect for: make stack-up, make spec-test, CI validation"
            echo "  • Set up GitHub Actions runner: ./config.sh --labels self-hosted,macstudio"
            echo "  • Use for production-like testing and heavy workloads"
            ;;
        "laptop")
            echo "  • Perfect for: make spec-new, UI development, fast iteration"
            echo "  • Use VITE_API_BASE=http://studio-ip:13370 for development"
            echo "  • Author SPECs, push to trigger Studio validation"
            ;;
        "server")
            echo "  • Server environment detected"
            echo "  • Suitable for: CI/CD, production deployments, automated testing"
            echo "  • Container runtime and development tools available"
            ;;
        *)
            echo "  • Basic development capabilities detected"
            echo "  • May require additional tool installation for full functionality"
            ;;
    esac
}

main(){
    log "System Detection and Environment Validation"
    echo ""
    
    # Detect system capabilities
    detect_system
    echo ""
    
    # Check container runtime
    check_container_runtime
    echo ""
    
    # Check development tools
    check_development_tools
    echo ""
    
    # Get system role and deployment status for recommendations
    local system_info=$(detect_system)
    local system_role=$(echo "$system_info" | grep "SYSTEM_ROLE=" | cut -d= -f2)
    local is_deployment=$(echo "$system_info" | grep "SYSTEM_IS_DEPLOYMENT=" | cut -d= -f2)
    recommend_actions "$system_role" "$is_deployment"
}

# If sourced, just define functions. If executed, run main.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
