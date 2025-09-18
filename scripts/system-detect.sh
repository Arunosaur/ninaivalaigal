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
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local macos_version=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
        system_info="macOS $macos_version"
        
        # Detect Mac model
        local model=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Model Name" | cut -d: -f2 | xargs || echo "unknown")
        local chip=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Chip" | cut -d: -f2 | xargs || echo "unknown")
        local memory=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Memory" | cut -d: -f2 | xargs || echo "unknown")
        
        echo "SYSTEM_OS=macOS"
        echo "SYSTEM_VERSION=$macos_version"
        echo "SYSTEM_MODEL=$model"
        echo "SYSTEM_CHIP=$chip"
        echo "SYSTEM_MEMORY=$memory"
        
        # Determine if this is likely the Mac Studio
        if [[ "$model" == *"Mac Studio"* ]] || [[ "$chip" == *"M1 Ultra"* ]] || [[ "$memory" == *"128 GB"* ]]; then
            echo "SYSTEM_ROLE=studio"
            echo "SYSTEM_CAPABILITIES=heavy_validation,ci_runner,production_stack"
        else
            echo "SYSTEM_ROLE=laptop"
            echo "SYSTEM_CAPABILITIES=development,authoring,hot_reload"
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        system_info="Linux"
        echo "SYSTEM_OS=linux"
        echo "SYSTEM_ROLE=server"
        echo "SYSTEM_CAPABILITIES=ci_runner,production_stack"
    else
        system_info="Unknown OS"
        echo "SYSTEM_OS=unknown"
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
    
    log "Recommendations for $system_role:"
    
    case "$system_role" in
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
        *)
            echo "  • Basic development capabilities detected"
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
    
    # Get system role for recommendations
    local system_role=$(detect_system | grep "SYSTEM_ROLE=" | cut -d= -f2)
    recommend_actions "$system_role"
}

# If sourced, just define functions. If executed, run main.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
