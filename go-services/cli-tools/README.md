# Ninaivalaigal CLI Tools

> **Developer A Task #38** - Comprehensive command-line interface for managing and interacting with Ninaivalaigal microservices.

A powerful, unified CLI tool that provides seamless access to Memory Service, GraphOps Service, Load Testing, Health Monitoring, and Service Management capabilities.

## 🚀 Quick Start

### Installation

```bash
# Build from source
make build

# Install to system (requires sudo)
make install

# Or run directly
./nina --help
```

### Docker Usage

```bash
# Build Docker image
make docker-build

# Run in container
docker run -it --rm ninaivalaigal/cli-tools:latest

# Interactive mode in container
docker run -it --rm ninaivalaigal/cli-tools:latest interactive
```

## 📋 Features

### 🧠 Memory Operations
- **Store Memories**: `nina memory remember "Important information"`
- **Search Memories**: `nina memory recall "search query"`
- **List Memories**: `nina memory list --page 1 --page-size 20`
- **Export/Import**: `nina memory export --format json`

### 🕸️ Graph Operations
- **Execute Queries**: `nina graph query "MATCH (n) RETURN count(n)"`
- **Common Queries**: `nina graph query --common count-nodes`
- **Schema Management**: `nina graph schema show`
- **Data Visualization**: `nina graph visualize --output graph.png`

### 🏥 Health Monitoring
- **Check Services**: `nina health check`
- **Watch Health**: `nina health watch --interval 30`
- **Service Details**: `nina health detail gateway`
- **Health Summary**: `nina health summary`

### 🚀 Load Testing
- **HTTP Tests**: `nina loadtest http --url http://localhost:8080`
- **Scenario Tests**: `nina loadtest scenario --file scenarios/grpc-gateway.json`
- **Quick Tests**: `nina loadtest quick gateway`
- **Test Profiles**: `nina loadtest profile stress --target memory`

### ⚙️ Configuration Management
- **Show Config**: `nina config show`
- **Set Values**: `nina config set services.memory.url http://localhost:8081`
- **Profile Management**: `nina config profile use production`
- **Initialize**: `nina config init --example`

### 🔧 Service Management
- **Start Services**: `nina server start gateway load-tester`
- **Monitor Status**: `nina server status`
- **View Logs**: `nina server logs gateway --follow`
- **Build Services**: `nina server build --clean`

### 🎯 Interactive Mode
- **Guided Workflows**: `nina interactive`
- **Memory Assistant**: `nina interactive memory`
- **Graph Explorer**: `nina interactive graph`
- **Setup Wizard**: `nina interactive setup`

## 📚 Command Reference

### Global Flags
- `--config`: Configuration file path
- `--verbose, -v`: Enable verbose logging
- `--output, -o`: Output format (table, json, yaml)
- `--config-dir`: Configuration directory

### Memory Commands

```bash
# Store a memory
nina memory remember "Deploy new feature" --context "development" --metadata '{"priority":"high"}'

# Search memories
nina memory recall "deployment" --limit 10 --threshold 0.8

# List with pagination
nina memory list --page 2 --page-size 50 --context "development"

# Advanced search
nina memory search --text "bug fix" --metadata '{"status":"resolved"}'

# Statistics
nina memory stats

# Export data
nina memory export --format json --output memories.json --context "production"
```

### Graph Commands

```bash
# Execute Cypher query
nina graph query "MATCH (m:Memory) RETURN m LIMIT 5"

# Use parameters
nina graph query "MATCH (m:Memory) WHERE m.context = $ctx RETURN m" --params '{"ctx":"dev"}'

# Common queries
nina graph query --common node-types
nina graph query --common count-relations

# Schema operations
nina graph schema show
nina graph schema labels
nina graph schema relationships

# Index management
nina graph index list
nina graph index create Memory content

# Export graph data
nina graph export --format graphml --output graph.xml
```

### Health Commands

```bash
# Check all services
nina health check

# Check specific services
nina health check gateway memory

# Continuous monitoring
nina health watch --interval 30 --count 10

# Detailed service info
nina health detail memory

# JSON output for automation
nina health check --json
```

### Load Testing Commands

```bash
# HTTP load test
nina loadtest http --url http://localhost:8080/api/v1/memory/health \
  --concurrency 50 --requests 1000 --duration 60s

# Scenario-based test
nina loadtest scenario --file scenarios/grpc-gateway.json \
  --concurrency 100 --duration 300s

# Predefined profiles
nina loadtest profile smoke --target gateway
nina loadtest profile stress --target memory --url http://localhost:8081

# Quick validation
nina loadtest quick memory
nina loadtest validate http://localhost:8080
```

### Configuration Commands

```bash
# View current configuration
nina config show
nina config show services.memory.url

# Set configuration values
nina config set services.memory.url http://localhost:8081 --global
nina config set output.format json

# Profile management
nina config profile list
nina config profile show production
nina config profile use local

# Configuration validation
nina config validate

# Export/Import
nina config export --output nina-config.yaml
nina config import --input nina-config.yaml --merge
```

### Server Management Commands

```bash
# Start services
nina server start gateway --detach --rebuild
nina server start load-tester --env production

# Stop services
nina server stop gateway load-tester
nina server stop --force

# Restart with rebuild
nina server restart --rebuild

# Monitor services
nina server status
nina server logs gateway --follow --tail 100

# Build services
nina server build gateway load-tester --clean
```

## 🎛️ Configuration Profiles

### Local Development (Default)
```yaml
services:
  memory:
    url: "http://localhost:8081"
    timeout: "30s"
  graphops:
    url: "http://localhost:8082"
    timeout: "60s"
  gateway:
    url: "http://localhost:8080"
    timeout: "30s"
```

### Docker Compose
```yaml
services:
  memory:
    url: "http://memory-service:8081"
  graphops:
    url: "http://graphops-service:8082"
  gateway:
    url: "http://grpc-gateway:8080"
```

### Production
```yaml
services:
  memory:
    url: "https://memory.ninaivalaigal.com"
    timeout: "60s"
    auth:
      type: "bearer"
      token: "${NINA_TOKEN}"
  graphops:
    url: "https://graphops.ninaivalaigal.com"
    timeout: "120s"
    auth:
      type: "bearer"
      token: "${NINA_TOKEN}"
```

## 🔧 Development

### Build Commands

```bash
# Development build
make build

# Run tests
make test
make test-coverage

# Code quality
make validate  # runs fmt, vet, lint, test
make security  # security scan

# Build all platforms
make build-all

# Release build
make release-build
make release-package
```

### Integration Testing

```bash
# Setup test services
make setup-services

# Run integration tests
make integration-test
make smoke-test

# Cleanup
make teardown-services
```

## 📊 Advanced Usage

### Automation & Scripting

```bash
# JSON output for scripts
nina health check --json | jq '.[] | select(.status != "healthy")'

# Configuration in scripts
export NINA_SERVICES_MEMORY_URL="http://memory:8081"
nina memory list --output json

# Batch operations
nina memory export --format json | \
nina memory import --input - --merge
```

### Load Testing Scenarios

Create custom scenario files:

```json
{
  "name": "api-stress-test",
  "base_url": "http://localhost:8080",
  "endpoints": [
    {
      "path": "/api/v1/memory/remember",
      "method": "POST",
      "body": "{\"content\":\"Test memory\"}",
      "weight": 60
    },
    {
      "path": "/api/v1/memory/recall?q=test",
      "method": "GET",
      "weight": 40
    }
  ]
}
```

### Interactive Workflows

```bash
# Start interactive mode
nina interactive

# Specific interactive modules
nina interactive memory    # Memory operations wizard
nina interactive graph     # Graph query builder
nina interactive health    # Health monitoring dashboard
nina interactive setup     # First-time setup wizard
```

## 🐳 Docker Integration

### Multi-stage Build
- **Builder stage**: Go 1.21 with full build tools
- **Runtime stage**: Alpine Linux with minimal dependencies
- **Security**: Non-root user, minimal attack surface
- **Size**: Optimized for small image size

### Container Usage

```bash
# Run with host network (access local services)
docker run --network host ninaivalaigal/cli-tools:latest health check

# Mount config directory
docker run -v ~/.nina:/home/nina/.nina ninaivalaigal/cli-tools:latest config show

# Interactive mode
docker run -it ninaivalaigal/cli-tools:latest interactive
```

## 🔐 Security Features

- **Authentication**: Bearer token, API key, and basic auth support
- **TLS**: Full TLS/SSL support for HTTPS connections
- **Configuration**: Secure configuration file handling
- **Secrets**: Environment variable support for sensitive data
- **Validation**: Input validation and sanitization

## 📈 Monitoring & Observability

- **Health Checks**: Comprehensive service health monitoring
- **Metrics**: Built-in metrics collection and export
- **Logging**: Structured logging with configurable levels
- **Tracing**: Request tracing for debugging

## 🛠️ Extensibility

The CLI is designed for extensibility:

- **Plugin Architecture**: Easy to add new commands
- **Configuration**: Flexible configuration system
- **Output Formats**: Multiple output formats (table, JSON, YAML)
- **Profiles**: Environment-specific configurations

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make validate`
5. Submit a pull request

## 🆘 Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Help**: `nina --help` or `nina [command] --help`
- **Interactive**: `nina interactive` for guided workflows

---

**Ninaivalaigal CLI Tools** - Comprehensive command-line interface for unified microservice management. 🚀
