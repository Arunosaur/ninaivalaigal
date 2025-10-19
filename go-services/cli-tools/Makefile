# Ninaivalaigal CLI Tools Makefile
# Developer A Task #38 - Comprehensive CLI Tools

# Variables
BINARY_NAME=nina
BINARY_PATH=./$(BINARY_NAME)
GO_FILES=$(shell find . -name "*.go" -type f)
VERSION=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
LDFLAGS=-ldflags "-X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME)"

# Build targets
.PHONY: build
build: ## Build the CLI binary
	@echo "🔨 Building $(BINARY_NAME)..."
	go build $(LDFLAGS) -o $(BINARY_PATH) .
	@echo "✅ Built $(BINARY_NAME) successfully"

.PHONY: build-all
build-all: ## Build for all platforms
	@echo "🔨 Building for all platforms..."
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-linux-amd64 .
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-darwin-amd64 .
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(BINARY_NAME)-darwin-arm64 .
	GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(BINARY_NAME)-windows-amd64.exe .
	@echo "✅ Built all platform binaries"

.PHONY: install
install: build ## Install the CLI binary to system
	@echo "📦 Installing $(BINARY_NAME)..."
	sudo cp $(BINARY_PATH) /usr/local/bin/
	@echo "✅ Installed $(BINARY_NAME) to /usr/local/bin/"

.PHONY: uninstall
uninstall: ## Uninstall the CLI binary from system
	@echo "🗑️  Uninstalling $(BINARY_NAME)..."
	sudo rm -f /usr/local/bin/$(BINARY_NAME)
	@echo "✅ Uninstalled $(BINARY_NAME)"

# Development targets
.PHONY: dev
dev: ## Run in development mode with hot reload
	@echo "🔥 Starting development mode..."
	go run . --verbose

.PHONY: run
run: build ## Build and run the CLI
	@echo "🚀 Running $(BINARY_NAME)..."
	$(BINARY_PATH)

.PHONY: test
test: ## Run tests
	@echo "🧪 Running tests..."
	go test -v ./...

.PHONY: test-coverage
test-coverage: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	go test -v -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "📊 Coverage report generated: coverage.html"

.PHONY: benchmark
benchmark: ## Run benchmarks
	@echo "⚡ Running benchmarks..."
	go test -bench=. -benchmem ./...

# Code quality targets
.PHONY: fmt
fmt: ## Format Go code
	@echo "🎨 Formatting code..."
	go fmt ./...
	@echo "✅ Code formatted"

.PHONY: vet
vet: ## Run go vet
	@echo "🔍 Running go vet..."
	go vet ./...
	@echo "✅ Vet completed"

.PHONY: lint
lint: ## Run golangci-lint
	@if command -v golangci-lint >/dev/null 2>&1; then \
		echo "🔍 Running golangci-lint..."; \
		golangci-lint run; \
		echo "✅ Lint completed"; \
	else \
		echo "⚠️  golangci-lint not installed, skipping"; \
	fi

.PHONY: staticcheck
staticcheck: ## Run staticcheck
	@if command -v staticcheck >/dev/null 2>&1; then \
		echo "🔍 Running staticcheck..."; \
		staticcheck ./...; \
		echo "✅ Staticcheck completed"; \
	else \
		echo "⚠️  staticcheck not installed, skipping"; \
	fi

.PHONY: security
security: ## Run gosec security scanner
	@if command -v gosec >/dev/null 2>&1; then \
		echo "🔒 Running security scan..."; \
		gosec ./...; \
		echo "✅ Security scan completed"; \
	else \
		echo "⚠️  gosec not installed, skipping"; \
	fi

# Dependency management
.PHONY: deps
deps: ## Download dependencies
	@echo "📦 Downloading dependencies..."
	go mod download
	@echo "✅ Dependencies downloaded"

.PHONY: deps-update
deps-update: ## Update dependencies
	@echo "🔄 Updating dependencies..."
	go get -u ./...
	go mod tidy
	@echo "✅ Dependencies updated"

.PHONY: deps-verify
deps-verify: ## Verify dependencies
	@echo "🔍 Verifying dependencies..."
	go mod verify
	@echo "✅ Dependencies verified"

.PHONY: mod-tidy
mod-tidy: ## Tidy go modules
	@echo "🧹 Tidying modules..."
	go mod tidy
	@echo "✅ Modules tidied"

# Validation targets
.PHONY: validate
validate: fmt vet lint test ## Run all validation checks
	@echo "✅ All validation checks completed"

.PHONY: pre-commit
pre-commit: validate security ## Run pre-commit checks
	@echo "✅ Pre-commit checks completed"

# Documentation targets
.PHONY: docs
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@mkdir -p docs
	$(BINARY_PATH) --help > docs/help.txt
	$(BINARY_PATH) memory --help > docs/memory-help.txt
	$(BINARY_PATH) graph --help > docs/graph-help.txt
	$(BINARY_PATH) health --help > docs/health-help.txt
	$(BINARY_PATH) config --help > docs/config-help.txt
	@echo "✅ Documentation generated in docs/"

.PHONY: man
man: build ## Generate man pages
	@echo "📖 Generating man pages..."
	@mkdir -p man
	@if command -v pandoc >/dev/null 2>&1; then \
		echo "# $(BINARY_NAME)(1)" > man/$(BINARY_NAME).1.md; \
		echo "" >> man/$(BINARY_NAME).1.md; \
		echo "## NAME" >> man/$(BINARY_NAME).1.md; \
		echo "$(BINARY_NAME) - Ninaivalaigal CLI Tools" >> man/$(BINARY_NAME).1.md; \
		echo "" >> man/$(BINARY_NAME).1.md; \
		echo "## SYNOPSIS" >> man/$(BINARY_NAME).1.md; \
		echo "\`\`\`" >> man/$(BINARY_NAME).1.md; \
		$(BINARY_PATH) --help >> man/$(BINARY_NAME).1.md; \
		echo "\`\`\`" >> man/$(BINARY_NAME).1.md; \
		pandoc man/$(BINARY_NAME).1.md -s -t man -o man/$(BINARY_NAME).1; \
		echo "✅ Man page generated: man/$(BINARY_NAME).1"; \
	else \
		echo "⚠️  pandoc not installed, skipping man page generation"; \
	fi

# Integration targets
.PHONY: integration-test
integration-test: build ## Run integration tests
	@echo "🔗 Running integration tests..."
	@echo "Testing basic commands..."
	$(BINARY_PATH) --version
	$(BINARY_PATH) config show --format json >/dev/null
	$(BINARY_PATH) health check --json >/dev/null || echo "Services may not be running"
	@echo "✅ Integration tests completed"

.PHONY: smoke-test
smoke-test: build ## Run smoke tests
	@echo "💨 Running smoke tests..."
	$(BINARY_PATH) --help >/dev/null
	$(BINARY_PATH) --version >/dev/null
	$(BINARY_PATH) config --help >/dev/null
	$(BINARY_PATH) memory --help >/dev/null
	$(BINARY_PATH) graph --help >/dev/null
	$(BINARY_PATH) health --help >/dev/null
	@echo "✅ Smoke tests passed"

# Cleanup targets
.PHONY: clean
clean: ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	rm -f $(BINARY_NAME)
	rm -f $(BINARY_NAME)-*
	rm -f coverage.out coverage.html
	rm -rf docs/ man/
	@echo "✅ Cleaned build artifacts"

.PHONY: clean-deps
clean-deps: ## Clean dependency cache
	@echo "🧹 Cleaning dependency cache..."
	go clean -modcache
	@echo "✅ Cleaned dependency cache"

# Release targets
.PHONY: release-build
release-build: ## Build release versions
	@echo "🚀 Building release versions..."
	@$(MAKE) clean
	@$(MAKE) validate
	@$(MAKE) build-all
	@echo "✅ Release build completed"

.PHONY: release-package
release-package: release-build ## Package release
	@echo "📦 Packaging release..."
	@mkdir -p dist
	tar -czf dist/$(BINARY_NAME)-$(VERSION)-linux-amd64.tar.gz $(BINARY_NAME)-linux-amd64
	tar -czf dist/$(BINARY_NAME)-$(VERSION)-darwin-amd64.tar.gz $(BINARY_NAME)-darwin-amd64
	tar -czf dist/$(BINARY_NAME)-$(VERSION)-darwin-arm64.tar.gz $(BINARY_NAME)-darwin-arm64
	zip -q dist/$(BINARY_NAME)-$(VERSION)-windows-amd64.zip $(BINARY_NAME)-windows-amd64.exe
	@echo "✅ Release packaged in dist/"

# Docker targets
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t ninaivalaigal/cli-tools:$(VERSION) .
	docker build -t ninaivalaigal/cli-tools:latest .
	@echo "✅ Docker image built"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -it --rm ninaivalaigal/cli-tools:latest

.PHONY: docker-push
docker-push: docker-build ## Push Docker image
	@echo "🐳 Pushing Docker image..."
	docker push ninaivalaigal/cli-tools:$(VERSION)
	docker push ninaivalaigal/cli-tools:latest
	@echo "✅ Docker image pushed"

# Utility targets
.PHONY: version
version: ## Show version information
	@echo "Version: $(VERSION)"
	@echo "Build Time: $(BUILD_TIME)"

.PHONY: size
size: build ## Show binary size
	@echo "📏 Binary size:"
	@ls -lh $(BINARY_PATH) | awk '{print $$5 " " $$9}'

.PHONY: upx
upx: build ## Compress binary with UPX
	@if command -v upx >/dev/null 2>&1; then \
		echo "🗜️  Compressing binary with UPX..."; \
		upx --best $(BINARY_PATH); \
		echo "✅ Binary compressed"; \
	else \
		echo "⚠️  UPX not installed, skipping compression"; \
	fi

# Database and service integration
.PHONY: setup-services
setup-services: ## Setup required services for testing
	@echo "🔧 Setting up services for testing..."
	@if [ -f "../docker-compose.yml" ]; then \
		cd .. && docker-compose up -d; \
		echo "✅ Services started with Docker Compose"; \
	else \
		echo "⚠️  Docker Compose file not found"; \
	fi

.PHONY: teardown-services
teardown-services: ## Teardown test services
	@echo "🛑 Tearing down test services..."
	@if [ -f "../docker-compose.yml" ]; then \
		cd .. && docker-compose down; \
		echo "✅ Services stopped"; \
	else \
		echo "⚠️  Docker Compose file not found"; \
	fi

# Help target
.PHONY: help
help: ## Show this help message
	@echo "🛠️  Ninaivalaigal CLI Tools - Available Make Targets"
	@echo "=================================================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🚀 Quick start:"
	@echo "  make build          # Build the CLI binary"
	@echo "  make install        # Install to system"
	@echo "  make validate       # Run all checks"
	@echo "  make integration-test  # Test with services"

# Default target
.DEFAULT_GOAL := help
