#!/bin/bash

# Quick build test for Developer A components
echo "🔨 Quick Build Test"
echo "=================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${BLUE}🔄 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Test gRPC Gateway
echo ""
print_step "Testing gRPC Gateway build..."
cd go-services/grpc-gateway || exit

# Check if Go is available
if ! command -v go &> /dev/null; then
    print_error "Go not found. Please install Go 1.21+"
    exit 1
fi

print_step "Go version: $(go version)"

# Check go.mod
if [ -f "go.mod" ]; then
    print_success "go.mod found"
    cat go.mod | head -5
else
    print_error "go.mod not found"
    exit 1
fi

# Try go mod tidy
print_step "Running go mod tidy..."
if go mod tidy; then
    print_success "go mod tidy successful"
else
    print_error "go mod tidy failed"
    exit 1
fi

# Try go build
print_step "Attempting build..."
if go build -o grpc-gateway .; then
    print_success "gRPC Gateway built successfully!"

    # Check if binary exists
    if [ -f "./grpc-gateway" ]; then
        print_success "Binary created: ./grpc-gateway"
        ls -la grpc-gateway
    fi
else
    print_error "Build failed"
    exit 1
fi

cd - > /dev/null || exit

print_success "Quick build test completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Run full test suite: ./run_all_tests.sh"
echo "2. Test other components"
echo "3. Run integration tests"
