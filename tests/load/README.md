# Load Testing with Dynamic Configuration Discovery

This directory contains load tests that automatically discover service ports and IPs based on the container runtime (Docker/Colima/Apple Container CLI) and environment (dev/test/prod).

## Features

- ✅ **Dynamic Port Discovery**: Automatically reads from `config/ports.nv.yaml`
- ✅ **Runtime Detection**: Detects Docker, Colima, or Apple Container CLI
- ✅ **Environment Detection**: Uses `NINA_ENV` or defaults to `dev`
- ✅ **Secret Management**: Loads secrets from `.env.{env}` files
- ✅ **Multi-Service Support**: Works with microservices architecture

## Usage

### Basic Load Test

```bash
# Automatically detects runtime and environment
locust -f tests/load/test_billing_performance.py --headless --users 100 --spawn-rate 10 --run-time 30m
```

### Override Runtime

```bash
# Force Apple Container CLI
NINA_RUNTIME=apple locust -f tests/load/test_billing_performance.py --headless --users 100

# Force Docker
NINA_RUNTIME=docker locust -f tests/load/test_billing_performance.py --headless --users 100

# Force Colima
NINA_RUNTIME=colima locust -f tests/load/test_billing_performance.py --headless --users 100
```

### Override Environment

```bash
# Test against test environment
NINA_ENV=test locust -f tests/load/test_billing_performance.py --headless --users 100

# Test against prod environment
NINA_ENV=prod locust -f tests/load/test_billing_performance.py --headless --users 100
```

### Container IP Discovery (Default)

**Container IPs are used by default** for cloud compatibility. The discovery automatically:
- Finds container IPs for running containers
- Falls back to `localhost` if container not found
- Works across Docker, Colima, and Apple Container CLI

```python
# Default behavior - uses container IPs
from config_discovery import get_service_config

config = get_service_config()  # use_container_ips=True by default

# Force localhost (for local development)
config = get_service_config(use_container_ips=False)
```

## Configuration Discovery

The `config_discovery.py` module:

1. **Detects Runtime**: Checks for running containers in each runtime
2. **Detects Environment**: Uses `NINA_ENV` or `ENVIRONMENT` env var
3. **Loads Ports**: Reads from `config/ports.nv.yaml`
4. **Loads Secrets**: Reads from `.env.{env}` files
5. **Returns Config**: Provides service URLs and auth config

## Port Allocation

Ports are allocated according to `config/ports.nv.yaml`:

| Runtime | Dev Core API | Dev Business Service |
|---------|--------------|----------------------|
| Docker  | 13370        | 13371                |
| Colima  | 13380        | 13381                |
| Apple   | 13390        | 13391                |

## Service URLs

The config discovery provides:

- `core_api.url`: Core API service (auth, users, teams)
- `business_service.url`: Business Service (billing, analytics)
- `admin_vendor.url`: Admin/Vendor service
- `memory_service.url`: Memory Service
- `graph_service.url`: Graph Service
- `gateway.url`: API Gateway

## Environment Variables

### Runtime Detection
- `NINA_RUNTIME`: Override runtime (`docker`, `colima`, `apple`)

### Environment Selection
- `NINA_ENV`: Environment (`dev`, `test`, `prod`)
- `ENVIRONMENT`: Alternative env var for environment

### Secrets
Secrets are loaded from `.env.{env}` files:
- `.env.dev` for development
- `.env.test` for testing
- `.env.prod` for production

Common secrets:
- `NINA_JWT_SECRET`: JWT signing secret
- `DATABASE_URL`: Database connection string
- `STRIPE_SECRET_KEY`: Stripe API key

## Example

```python
from config_discovery import get_service_config, get_core_api_url, get_business_service_url

# Get full config
config = get_service_config()
print(f"Runtime: {config['runtime']}")
print(f"Environment: {config['environment']}")

# Get service URLs
core_api = get_core_api_url(config)
business_service = get_business_service_url(config)

# Use in tests
response = requests.get(f"{core_api}/health")
```

## Troubleshooting

### Wrong Runtime Detected

```bash
# Explicitly set runtime
NINA_RUNTIME=apple locust -f tests/load/test_billing_performance.py ...
```

### Ports Not Found

Check that `config/ports.nv.yaml` exists and contains the correct runtime/environment combination.

### Secrets Not Loaded

Ensure `.env.{env}` file exists in project root with required secrets.

### Container IPs Not Working

Container IP discovery requires containers to be running. If a container is not found, it automatically falls back to `localhost`. To force `localhost` for all services, set `use_container_ips=False`:

```python
config = get_service_config(use_container_ips=False)
```

### Container IP Discovery Failing

If container IPs are not being discovered:
1. Verify containers are running: `container list` (Apple) or `docker ps` (Docker/Colima)
2. Check container names match pattern: `ninaivalaigal-{env}-{service}`
3. Review logs for discovery warnings
4. Fallback to localhost is automatic if discovery fails
