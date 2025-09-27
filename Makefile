# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb skip-mem0 with-mem0 with-ui logs backup db-stats pgb-stats restore verify-backup verify-latest cleanup-backups cleanup-backups-dry spec-new spec-test system-info test-mem0-auth ui-up ui-down ui-status sanity-check validate-production start stop health metrics dev-up dev-down dev-logs dev-status tunnel-start tunnel-stop deploy-aws-vm deploy-gcp-vm deploy-azure-vm deploy-aws deploy-gcp deploy-azure k8s-deploy k8s-status k8s-logs k8s-delete build-images install uninstall ci-test release release-local nina-stack-up nina-stack-down nina-stack-status nina-db-only

## start full stack: DB → Redis → PgBouncer → eM → API → UI
stack-up:
	@$(SCRIPTS)/nv-stack-start.sh

## stop stack: UI → API → Mem0 → PgBouncer → Redis → DB
stack-down:
	@$(SCRIPTS)/nv-stack-stop.sh

## show status of all 5 services
stack-status:
	@$(SCRIPTS)/nv-stack-status.sh

## comprehensive container health monitoring
health-check:
	@$(SCRIPTS)/nv-container-health.sh check

## auto-restart unhealthy containers
health-restart:
	@$(SCRIPTS)/nv-container-health.sh auto-restart

## continuous health monitoring (30s interval)
health-monitor:
	@$(SCRIPTS)/nv-container-health.sh continuous 30 true

## bring up only the database
db-only:
	@$(SCRIPTS)/nv-stack-start.sh --db-only

## bring up DB + PgBouncer but skip Mem0 and API
skip-api:
	@$(SCRIPTS)/nv-stack-start.sh --skip-api

## bring up DB + API but skip PgBouncer
skip-pgb:
	@$(SCRIPTS)/nv-stack-start.sh --skip-pgb

## bring up DB + PgBouncer + API but skip eM
skip-em:
	@$(SCRIPTS)/nv-stack-start.sh --skip-em

## bring up DB + PgBouncer + eM but skip API
with-em:
	@$(SCRIPTS)/nv-stack-start.sh --with-em --skip-api

## bring up full stack with UI
with-ui:
	@$(SCRIPTS)/nv-stack-start.sh --with-ui

## tail logs for all containers
logs:
	@echo "== DB logs ==";        -container logs -f nv-db & \
	 echo "== PgBouncer logs =="; -container logs -f nv-pgbouncer & \
	 echo "== eM logs ==";        -container logs -f nv-em & \
	 echo "== API logs ==";       -container logs -f nv-api & \
	 echo "== UI logs ==";        -container logs -f nv-ui & wait

## backup database
backup:
	@$(SCRIPTS)/backup-db.sh

## show database statistics
db-stats:
	@$(SCRIPTS)/db-stats.sh

## show PgBouncer statistics
pgb-stats:
	@echo "SHOW STATS;" | psql "postgresql://$(POSTGRES_USER):$$POSTGRES_PASSWORD@127.0.0.1:$(PGBOUNCER_PORT)/pgbouncer"

## restore database from backup (usage: make restore BACKUP_FILE=path/to/backup.dump)
restore:
	@$(SCRIPTS)/restore-db.sh $(BACKUP_FILE)

## verify backup integrity (usage: make verify-backup BACKUP_FILE=path/to/backup.dump)
verify-backup:
	@$(SCRIPTS)/verify-backup.sh $(BACKUP_FILE)

## verify latest backup
verify-latest:
	@$(SCRIPTS)/verify-backup.sh latest

## cleanup old backups (usage: make cleanup-backups RETENTION_DAYS=14)
cleanup-backups:
	@$(SCRIPTS)/cleanup-backups.sh $(if $(RETENTION_DAYS),--retention-days $(RETENTION_DAYS),)

## dry run backup cleanup
cleanup-backups-dry:
	@$(SCRIPTS)/cleanup-backups.sh --dry-run $(if $(RETENTION_DAYS),--retention-days $(RETENTION_DAYS),)

## create new SPEC (usage: make spec-new ID=013 NAME="memory-substrate-v2")
spec-new:
	@$(SCRIPTS)/spec-new.sh $(ID) $(NAME)

## test SPEC implementation (usage: make spec-test ID=013)
spec-test:
	@$(SCRIPTS)/spec-test.sh $(ID)

## detect system capabilities and provide recommendations
system-info:
	@$(SCRIPTS)/system-detect.sh

## test eM sidecar authentication
test-em-auth:
	@$(SCRIPTS)/test-em-auth.sh

## UI management targets
ui-up:
	@$(SCRIPTS)/nv-ui-start.sh

ui-down:
	@$(SCRIPTS)/nv-ui-stop.sh

ui-status:
	@$(SCRIPTS)/nv-ui-status.sh

## run comprehensive production readiness validation
sanity-check:
	@$(SCRIPTS)/sanity-check.sh

## alias for sanity-check
validate-production: sanity-check

## Apple Container CLI convenience aliases
start: stack-up

stop: stack-down

hdev-status:
	@echo "📊 Development Stack Status"
	@echo "=========================="
	@container ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(nv-|NAMES)"

## Redis Management Commands (SPEC-033)
redis-install:
	@echo "🔴 Installing Redis for ninaivalaigal..."
	@container run -d --name nv-redis -p 6379:6379 \
		-e REDIS_PASSWORD=nina_redis_dev_password \
		-v nv_redis_data:/data \
		redis:7-alpine redis-server --requirepass nina_redis_dev_password --maxmemory 256mb --maxmemory-policy allkeys-lru
	@echo "✅ Redis installed and running on port 6379"
	@echo "📊 Prometheus Metrics Summary"
	@echo "============================="
	@echo "🔗 Full metrics: http://localhost:13370/metrics"
	@echo ""
	@echo "📈 Key Performance Metrics:"
	@curl -s http://localhost:13370/metrics | grep -E "(http_requests_total|http_request_duration_seconds_count|process_resident_memory_bytes|app_uptime_seconds)" | head -10

## Docker Compose-style dev environment
dev-up:
	@echo "🚀 Starting development environment..."
	@$(SCRIPTS)/nv-stack-start.sh --skip-em
	@echo "✅ Development stack ready!"
	@echo "   Database: http://localhost:5433"
	@echo "   PgBouncer: http://localhost:6432"
	@echo "   API: http://localhost:13370"
	@echo ""
	@echo "Quick health check:"
	@make health

dev-down:
	@echo "🛑 Stopping development environment..."
	@$(SCRIPTS)/nv-stack-stop.sh

dev-logs:
	@echo "📋 Following logs for all containers..."
	@container logs -f nv-db & \
	 container logs -f nv-pgbouncer & \
	 container logs -f nv-api & \
	 wait

dev-status: stack-status

## Remote Access & Cloud Deployment
tunnel-start:
	@echo "🌐 Starting secure tunnel for remote access..."
	@echo "Usage: REMOTE_HOST=your-server.com make tunnel-start"
	@$(SCRIPTS)/nv-tunnel-start.sh

tunnel-stop:
	@echo "🛑 Stopping secure tunnels..."
	@$(SCRIPTS)/nv-tunnel-stop.sh

## Virtual Machine Deployment
deploy-aws-vm:
	@echo "🚀 Deploying to AWS EC2 VM..."
	@echo "Usage: KEY_NAME=my-key make deploy-aws-vm"
	@$(SCRIPTS)/deploy-aws.sh

deploy-gcp-vm:
	@echo "🚀 Deploying to GCP Compute Engine VM..."
	@echo "Usage: PROJECT_ID=my-project make deploy-gcp-vm"
	@$(SCRIPTS)/deploy-gcp.sh

deploy-azure-vm:
	@echo "🚀 Deploying to Azure VM..."
	@echo "Usage: RESOURCE_GROUP=my-rg make deploy-azure-vm"
	@$(SCRIPTS)/deploy-azure.sh

## Cloud-Native Container Services
deploy-aws:
	@echo "🚀 Deploying to AWS ECS..."
	@aws ecs update-service \
		--cluster ninaivalaigal-cluster \
		--service ninaivalaigal-api \
		--force-new-deployment

deploy-gcp:
	@echo "🚀 Deploying to Google Cloud Run..."
	@gcloud run deploy ninaivalaigal-api \
		--image=ghcr.io/arunosaur/ninaivalaigal-api:latest \
		--platform=managed \
		--region=us-central1 \
		--allow-unauthenticated

deploy-azure:
	@echo "🚀 Deploying to Azure Container Instances..."
	@az container create \
		--resource-group ninaivalaigal-rg \
		--name ninaivalaigal-api \
		--image ghcr.io/arunosaur/ninaivalaigal-api:latest \
		--cpu 1 --memory 1.5 \
		--dns-name-label ninaivalaigal-api \
		--ports 8080 \
		--restart-policy Always

## Kubernetes Deployment
k8s-deploy:
	@echo "🚀 Deploying to Kubernetes with GHCR images..."
	@kubectl apply -k k8s/
	@echo "✅ Deployed to Kubernetes namespace: ninaivalaigal"

k8s-status:
	@echo "📊 Kubernetes deployment status..."
	@kubectl get all -n ninaivalaigal

k8s-logs:
	@echo "📋 API logs from Kubernetes..."
	@kubectl logs -n ninaivalaigal -l app=ninaivalaigal-api --tail=50

k8s-delete:
	@echo "🗑️ Deleting Kubernetes deployment..."
	@kubectl delete -k k8s/ || true

## Terraform Infrastructure as Code
terraform-init-aws:
	@echo "🏗️ Initializing Terraform for AWS..."
	@cd terraform/aws && terraform init

terraform-plan-aws:
	@echo "📋 Planning Terraform deployment for AWS..."
	@cd terraform/aws && terraform plan

terraform-apply-aws:
	@echo "🚀 Applying Terraform deployment for AWS..."
	@cd terraform/aws && terraform apply

terraform-destroy-aws:
	@echo "🗑️ Destroying Terraform deployment for AWS..."
	@cd terraform/aws && terraform destroy

terraform-init-gcp:
	@echo "🏗️ Initializing Terraform for GCP..."
	@cd terraform/gcp && terraform init

terraform-plan-gcp:
	@echo "📋 Planning Terraform deployment for GCP..."
	@cd terraform/gcp && terraform plan

terraform-apply-gcp:
	@echo "🚀 Applying Terraform deployment for GCP..."
	@cd terraform/gcp && terraform apply

terraform-destroy-gcp:
	@echo "🗑️ Destroying Terraform deployment for GCP..."
	@cd terraform/gcp && terraform destroy

terraform-init-azure:
	@echo "🏗️ Initializing Terraform for Azure..."
	@cd terraform/azure && terraform init

terraform-plan-azure:
	@echo "📋 Planning Terraform deployment for Azure..."
	@cd terraform/azure && terraform plan

terraform-apply-azure:
	@echo "🚀 Applying Terraform deployment for Azure..."
	@cd terraform/azure && terraform apply

terraform-destroy-azure:
	@echo "🗑️ Destroying Terraform deployment for Azure..."
	@cd terraform/azure && terraform destroy

## Package Management & Installation
build-images:
	@echo "🏗️  Building container images..."
	@$(SCRIPTS)/build-images.sh

install:
	@echo "📦 Installing ninaivalaigal..."
	@./install.sh

uninstall:
	@echo "🗑️  Uninstalling ninaivalaigal..."
	@echo "This will remove container images and stop all services."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@make dev-down || true
	@container rmi nina-pgbouncer:arm64 nina-api:arm64 2>/dev/null || true
	@echo "✅ Ninaivalaigal uninstalled"

## Container Building with Validation
build-api:
	@echo "🔨 Building API with dependency validation..."
	./scripts/build-and-validate-api.sh

build-api-unsafe:
	@echo "⚠️  Building API without validation (NOT RECOMMENDED)"
	container build -t nina-api:arm64 -f Dockerfile.api .

## Working State Management
capture-state:
	@echo "📸 Capturing current working state..."
	./scripts/capture-working-state.sh

cleanup-images:
	@echo "🧹 Cleaning up unused container images..."
	./scripts/cleanup-unused-images.sh

## SPEC-011: Memory Lifecycle Management
migrate-lifecycle:
	@echo "🔄 Running SPEC-011 memory lifecycle migration..."
	@$(SCRIPTS)/run-migration.sh server/memory/db/migrations/0112_memory_lifecycle.sql

lifecycle-gc:
	@echo "🗑️  Running memory garbage collection..."
	@cd server && conda run -n nina python -m memory.lifecycle.cli gc

lifecycle-stats:
	@echo "📊 Memory lifecycle statistics..."
	@cd server && conda run -n nina python -m memory.lifecycle.cli stats

lifecycle-gc-dry-run:
	@echo "🔍 Memory garbage collection (dry run)..."
	@cd server && conda run -n nina python -m memory.lifecycle.cli gc --dry-run

## SPEC-021: GitOps Deployment via ArgoCD
setup-test-cluster:
	@echo "🚀 Setting up test Kubernetes cluster..."
	@./scripts/setup-test-cluster.sh

argocd-install:
	@echo "🚀 Installing ArgoCD for GitOps deployment..."
	@./scripts/argocd-install.sh

argocd-status:
	@echo "📊 Checking ArgoCD status..."
	@./scripts/argocd-status.sh

argocd-ui:
	@echo "🌐 Opening ArgoCD UI..."
	@if ! pgrep -f "kubectl.*port-forward.*argocd-server" > /dev/null; then \
		echo "Starting port-forward..."; \
		kubectl port-forward svc/argocd-server -n argocd 8080:443 > /dev/null 2>&1 & \
	fi
	@sleep 2
	@echo "🔗 ArgoCD UI: https://localhost:8080"
	@echo "👤 Username: admin"
	@echo "🔒 Password: see argocd/credentials.txt"

argocd-sync:
	@echo "🔄 Triggering manual sync for ninaivalaigal application..."
	@kubectl patch application ninaivalaigal -n argocd --type merge -p '{"operation":{"sync":{}}}'

argocd-uninstall:
	@echo "🗑️  Uninstalling ArgoCD..."
	@kubectl delete -f argocd/application.yaml --ignore-not-found=true
	@kubectl delete namespace argocd --ignore-not-found=true
	@pkill -f "kubectl.*port-forward.*argocd-server" || true
	@rm -f argocd/credentials.txt
	@echo "✅ ArgoCD uninstalled"

## CI/CD & Testing
ci-test:
	@echo "🧪 Running GitHub Actions locally with act..."
	@echo "This simulates the x86_64 CI environment"
	@if command -v act >/dev/null 2>&1; then \
		act -j dev-stack; \
	else \
		echo "❌ act not found. Install with: brew install act"; \
		echo "   Then run: make ci-test"; \
	fi

## Multi-Architecture Container Release
# Set your image name (replace with your actual registry)
IMAGE_NAME = ghcr.io/arunosaur/ninaivalaigal

release:
	@echo "🚀 Building and pushing multi-arch containers..."
	@echo "Building for ARM64 and x86_64 platforms"
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--push \
		-t $(IMAGE_NAME)-api:latest \
		-t $(IMAGE_NAME)-api:$$(shell date +%Y%m%d-%H%M%S) \
		-f Dockerfile.api .
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--push \
		-t $(IMAGE_NAME)-pgbouncer:latest \
		-t $(IMAGE_NAME)-pgbouncer:$$(shell date +%Y%m%d-%H%M%S) \
		-f Dockerfile.pgbouncer .
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--push \
		-t $(IMAGE_NAME)-postgres:latest \
		-t $(IMAGE_NAME)-postgres:$$(shell date +%Y%m%d-%H%M%S) \
		-f Dockerfile.postgres .
	@echo "✅ Multi-arch containers released!"

release-local:
	@echo "🧪 Building multi-arch containers locally (no push)..."
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--load \
		-t $(IMAGE_NAME)-api:local-test
	@echo "🔨 Building API with dependency validation..."
	./scripts/build-and-validate-api.sh

build-api-unsafe:
	@echo "⚠️  Building API without validation (NOT RECOMMENDED)"
	container build -t nina-api:arm64 -f Dockerfile.api .
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--load \
		-t $(IMAGE_NAME)-pgbouncer:local-test \
		-f Dockerfile.pgbouncer .
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--load \
		-t $(IMAGE_NAME)-postgres:local-test \
		-f Dockerfile.postgres .
	@echo "✅ Multi-arch containers built locally!"

## Redis Management Commands (SPEC-033)
redis-install:
	@echo "🔴 Installing Redis for ninaivalaigal..."
	@container run -d --name nv-redis -p 6379:6379 \
		-e REDIS_PASSWORD=nina_redis_dev_password \
		-v nv_redis_data:/data \
		redis:7-alpine redis-server --requirepass nina_redis_dev_password --maxmemory 256mb --maxmemory-policy allkeys-lru
	@echo "✅ Redis installed and running on port 6379"

redis-status:
	@echo "🔴 Redis Status Check"
	@echo "===================="
	@container exec nv-redis redis-cli -a nina_redis_dev_password ping || echo "❌ Redis not responding"
	@container exec nv-redis redis-cli -a nina_redis_dev_password info memory | grep used_memory_human || echo "❌ Cannot get memory info"

redis-test:
	@echo "🔴 Redis Performance Test"
	@echo "========================"
	@conda activate nina && python specs/033-redis-integration/scripts/redis_test.py

redis-cli:
	@echo "🔴 Redis CLI Access"
	@echo "=================="
	@container exec -it nv-redis redis-cli -a nina_redis_dev_password

redis-stop:
	@echo "🔴 Stopping Redis..."
	@container stop nv-redis || true
	@container rm nv-redis || true
	@echo "✅ Redis stopped and removed"

redis-logs:
	@echo "🔴 Redis Logs"
	@echo "============"
	@container logs -f nv-redis

## Redis Queue Management Commands (SPEC-033)
redis-worker:
	@echo "🔴 Starting Redis Queue Worker"
	@echo "=============================="
	@conda activate nina && cd server && python -m rq worker --url redis://:nina_redis_dev_password@localhost:6379/0

redis-worker-dashboard:
	@echo "🔴 Starting RQ Dashboard"
	@echo "======================="
	@conda activate nina && rq-dashboard --redis-url redis://:nina_redis_dev_password@localhost:6379/0

redis-queue-stats:
	@echo "🔴 Redis Queue Statistics"
	@echo "========================"
	@curl -s http://localhost:13370/queue/stats | jq . || echo "❌ API not responding"

redis-queue-health:
	@echo "🔴 Redis Queue Health Check"
	@echo "=========================="
	@curl -s http://localhost:13370/queue/health | jq . || echo "❌ API not responding"

## Memory Relevance Testing Commands (SPEC-031)
test-relevance:
	@echo "🧠 Testing Memory Relevance Engine"
	@echo "=================================="
	@echo "Testing relevant memories endpoint..."
	@curl -s "http://localhost:13370/memory/relevant?limit=5" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-relevance-stats:
	@echo "🧠 Testing Relevance Statistics"
	@echo "==============================="
	@curl -s "http://localhost:13370/memory/relevance/stats" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-memory-access:
	@echo "🧠 Testing Memory Access Tracking"
	@echo "================================="
	@curl -s -X POST "http://localhost:13370/memory/memories/test-memory-123/access?context=testing" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

## test memory preloading system (SPEC-038)
test-preloading:
	@echo "🧠 Testing Memory Preloading System (SPEC-038)"
	@conda run -n nina python scripts/test_preloading_system.py

## test feedback loop system (SPEC-040)
test-feedback:
	@echo "🔁 Testing Feedback Loop System (SPEC-040)"
	@conda run -n nina python scripts/test_feedback_system.py

## test intelligent suggestions system (SPEC-041)
test-suggestions:
	@echo "🧠 Testing Intelligent Suggestions System (SPEC-041)"
	@conda run -n nina python scripts/test_suggestions_system.py

## test memory health & orphaned token system (SPEC-042)
test-health:
	@echo "🏥 Testing Memory Health & Orphaned Token System (SPEC-042)"
	@conda run -n nina python scripts/test_memory_health_system.py

## test memory access control (ACL) system (SPEC-043)
test-acl:
	@echo "🔐 Testing Memory Access Control (ACL) Per Token System (SPEC-043)"
	@conda run -n nina python scripts/test_memory_acl_system.py

## test memory drift & diff detection system (SPEC-044)
test-drift:
	@echo "🔍 Testing Memory Drift & Diff Detection System (SPEC-044)"
	@conda run -n nina python scripts/test_memory_drift_system.py

## SPEC-051: Developer Experience Improvements
lint-fix:
	@echo "🔧 Auto-fixing code formatting issues (SPEC-051)"
	@ruff check --fix .
	@ruff format .
	@echo "✅ Code formatting fixed"

lint-explain:
	@echo "📋 Explaining lint issues (SPEC-051)"
	@ruff check . --output-format=github || true
	@echo "💡 Run 'make lint-fix' to auto-fix most issues"

## SPEC-052: Comprehensive Test Coverage & Edge Case Validation
test-all-edge-cases:
	@echo "🧪 Running comprehensive edge case tests (SPEC-052)"
	@echo "Testing core SPECs..."
	@pytest tests/core/ -v --tb=short || true
	@echo "Testing intelligence layer..."
	@pytest tests/intelligence/ -v --tb=short || true
	@echo "Testing infrastructure..."
	@pytest tests/infra/ -v --tb=short || true
	@echo "Testing edge cases..."
	@pytest tests/edge/ -v --tb=short || true

test-coverage-report:
	@echo "📊 Generating SPEC-wise coverage report (SPEC-052)"
	@pytest --cov=server --cov-report=html --cov-report=term-missing
	@echo "📁 Coverage report: htmlcov/index.html"

validate-top-5-specs:
	@echo "🎯 Validating top 5 critical SPECs (SPEC-052)"
	@echo "1. SPEC-001: Core Memory System"
	@pytest tests/core/test_spec_001_memory.py -v || echo "❌ SPEC-001 needs validation"
	@echo "2. SPEC-033: Redis Integration"
	@pytest tests/intelligence/test_spec_033_redis.py -v || echo "❌ SPEC-033 needs validation"
	@echo "3. SPEC-043: Memory ACL"
	@pytest tests/intelligence/test_spec_043_acl.py -v || echo "❌ SPEC-043 needs validation"
	@echo "4. SPEC-044: Memory Drift Detection"
	@pytest tests/intelligence/test_spec_044_drift.py -v || echo "❌ SPEC-044 needs validation"
	@echo "5. SPEC-031: Memory Relevance Ranking"
	@pytest tests/intelligence/test_spec_031_relevance.py -v || echo "❌ SPEC-031 needs validation"

test-auth:
	@echo "\n🧪 Running Authentication Validation Suite (SPEC-053)..."
	@python -m pytest tests/auth \
	  --tb=short \
	  --disable-warnings \
	  --maxfail=5 \
	  --capture=no \
	  --strict-markers

# Debug mode for auth troubleshooting
test-auth-debug:
	@echo "\n🔍 Running Auth Tests in Debug Mode (SPEC-053)..."
	AUTH_DEBUG=1 python -m pytest tests/auth -s -v --tb=long

# Quick auth smoke test
test-auth-smoke:
	@echo "\n⚡ Running Auth Smoke Tests (SPEC-053)..."
	@python -m pytest tests/auth/test_login.py tests/auth/test_signup.py -v

test-preload-status:
	@echo "🚀 Testing Preloading Status"
	@echo "============================"
	@curl -s "http://localhost:13370/memory/preload/status" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-preload-config:
	@echo "🚀 Testing Preloading Configuration"
	@echo "==================================="
	@curl -s "http://localhost:13370/memory/preload/config" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-preload-stats:
	@echo "🚀 Testing Preloading Statistics"
	@echo "==============================="
	@curl -s "http://localhost:13370/memory/preload/stats" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-preload-health:
	@echo "🚀 Testing Preloading Health"
	@echo "============================"
	@curl -s "http://localhost:13370/memory/preload/health" | jq . || echo "❌ API not responding"

## Intelligent Session Management Testing Commands (SPEC-045)
test-session-analytics:
	@echo "🔐 Testing Session Analytics"
	@echo "============================"
	@curl -s "http://localhost:13370/auth/session/analytics" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-session-recommendations:
	@echo "🔐 Testing Session Renewal Recommendations"
	@echo "=========================================="
	@curl -s "http://localhost:13370/auth/session/recommendations" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-session-status:
	@echo "🔐 Testing Session Status"
	@echo "========================="
	@curl -s "http://localhost:13370/auth/session/status" -H "Authorization: Bearer test-token" | jq . || echo "❌ API not responding"

test-session-health:
	@echo "🔐 Testing Session System Health"
	@echo "================================"
	@curl -s "http://localhost:13370/auth/session/health" | jq . || echo "❌ API not responding"

# Code Coverage Targets
.PHONY: test-coverage test-unit test-functional test-integration test-security test-performance coverage-report coverage-html coverage-dashboard

test-coverage:
	@echo "🧪 Running comprehensive test suite with coverage..."
	coverage run -m pytest tests/ -v
	coverage report --show-missing
	coverage html

test-unit:
	@echo "🔬 Running unit tests..."
	pytest tests/unit/ -v --tb=short

test-unit-enhanced:
	@echo "🔬 Running enhanced unit tests..."
	pytest tests/unit/test_*_enhanced.py -v --tb=short

test-functional:
	@echo "🌐 Running functional tests..."
	pytest tests/functional/ -v --tb=short

test-functional-enhanced:
	@echo "🌐 Running enhanced functional tests..."
	pytest tests/functional/test_*_enhanced.py -v --tb=short

test-integration:
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ -v --tb=short

test-security:
	@echo "🛡️ Running security tests..."
	pytest tests/security/ -v --tb=short

test-performance:
	@echo "🚀 Running performance benchmarks..."
	pytest tests/performance/ -v --benchmark-only

test-auth:
	@echo "🔐 Running authentication tests..."
	pytest tests/ -k "auth" -v --tb=short

test-memory:
	@echo "🧠 Running memory tests..."
	pytest tests/ -k "memory" -v --tb=short

test-rbac:
	@echo "🛡️ Running RBAC tests..."
	pytest tests/ -k "rbac" -v --tb=short

test-database:
	@echo "🗄️ Running database tests..."
	pytest tests/ -k "database" -v --tb=short

test-redis:
	@echo "🔴 Running Redis tests..."
	pytest tests/ -k "redis" -v --tb=short

test-observability:
	@echo "📊 Running observability tests..."
	pytest tests/ -k "observability" -v --tb=short

test-infrastructure:
	@echo "🏗️ Running infrastructure tests (database, redis, observability)..."
	pytest tests/ -k "database or redis or observability" -v --tb=short

benchmark-redis:
	@echo "⚡ Running Redis performance benchmarks..."
	pytest tests/performance/test_redis_benchmarks.py -v --benchmark-only --benchmark-sort=mean

benchmark-all:
	@echo "📊 Running all performance benchmarks..."
	pytest tests/performance/ -v --benchmark-only --benchmark-sort=mean --benchmark-json=benchmark_results.json

test-graph:
	@echo "🕸️ Running Apache AGE graph tests..."
	pytest server/graph/tests/ -v --tb=short

test-graph-nodes:
	@echo "🔵 Running graph node tests..."
	pytest server/graph/tests/cypher/test_node_queries.py -v --tb=short

test-graph-edges:
	@echo "🔗 Running graph edge tests..."
	pytest server/graph/tests/cypher/test_edge_queries.py -v --tb=short

benchmark-graph:
	@echo "⚡ Running graph performance benchmarks..."
	pytest server/graph/tests/ -v --benchmark-only --benchmark-sort=mean

test-spec-060:
	@echo "🎯 Running SPEC-060 Apache AGE implementation tests..."
	pytest server/graph/tests/ tests/unit/test_redis_enhanced.py -k "graph or age or cypher" -v --tb=short

## SPEC-061: Property Graph Intelligence Framework
test-graph-reasoner:
	@echo "🧠 Running graph reasoner tests..."
	pytest tests/unit/test_graph_reasoner_unit.py tests/functional/test_graph_reasoner_functional.py -v --tb=short

benchmark-reasoner:
	@echo "⚡ Running graph reasoner performance benchmarks..."
	pytest tests/performance/benchmark_reasoner.py --benchmark-only --benchmark-sort=mean -v

spec-061:
	@echo "🎯 Running complete SPEC-061 validation..."
	@make test-graph-reasoner && make benchmark-reasoner
	@echo "✅ SPEC-061 Property Graph Intelligence Framework validation complete"

test-graph-intelligence-api:
	@echo "🌐 Testing Graph Intelligence API endpoints..."
	pytest tests/unit/test_graph_intelligence_api.py -v --tb=short

## GraphOps Infrastructure Management (Dual Architecture)
build-graph-db-arm64:
	@echo "🏗️ Building Apache AGE + PostgreSQL image for ARM64 (Apple Container CLI)..."
	cd containers/graph-db && container build . -t ninaivalaigal-graph-db:arm64

build-graph-db-x86:
	@echo "🏗️ Building Apache AGE + PostgreSQL image for x86_64 (CI/Docker)..."
	cd containers/graph-db && docker buildx build --platform linux/amd64 . -t ninaivalaigal-graph-db:x86_64

build-graph-db: build-graph-db-arm64
	@echo "✅ Graph DB image built for current architecture"

start-graph-infrastructure: build-graph-db
	@echo "🚀 Starting graph infrastructure (Apache AGE + Redis)..."
	@echo "Starting Redis..."
	container run -d --name ninaivalaigal-graph-redis \
		-p 6381:6379 \
		redis:7-alpine redis-server --appendonly yes || true
	@echo "Starting Graph DB..."
	container run -d --name ninaivalaigal-graph-db \
		-p 5434:5432 \
		-e POSTGRES_DB=ninaivalaigal_graph \
		-e POSTGRES_USER=graphuser \
		-e POSTGRES_PASSWORD=${GRAPH_DB_PASSWORD:-graphpass} \
		-e POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256" \
		ninaivalaigal-graph-db:arm64 || true
	@echo "⏳ Waiting for services to be ready..."
	@sleep 20
	@make check-graph-health

stop-graph-infrastructure:
	@echo "🛑 Stopping graph infrastructure..."
	@echo "Stopping Graph DB..."
	container stop ninaivalaigal-graph-db || true
	container rm ninaivalaigal-graph-db || true
	@echo "Stopping Redis..."
	container stop ninaivalaigal-graph-redis || true
	container rm ninaivalaigal-graph-redis || true

restart-graph-infrastructure:
	@echo "🔄 Restarting graph infrastructure..."
	@make stop-graph-infrastructure
	@make start-graph-infrastructure

check-graph-health:
	@echo "🏥 Checking graph infrastructure health..."
	@echo "📊 Container Status:"
	@container list | grep -E "(ninaivalaigal-graph-db|ninaivalaigal-graph-redis)" || echo "No graph containers running"
	@echo "📊 Graph DB Status:"
	@container exec ninaivalaigal-graph-db pg_isready -U graphuser -d ninaivalaigal_graph || echo "❌ Graph DB not ready"
	@echo "📊 Redis Status:"
	@container exec ninaivalaigal-graph-redis redis-cli ping || echo "❌ Redis not ready"

graph-db-shell:
	@echo "🐘 Connecting to graph database..."
	container exec -it ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph

graph-redis-shell:
	@echo "📦 Connecting to graph Redis..."
	container exec -it ninaivalaigal-graph-redis redis-cli

init-graph-schema:
	@echo "🏗️ Initializing graph schema..."
	container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "SELECT * FROM graph_stats;"

clean-graph-data:
	@echo "🧹 Cleaning graph data (WARNING: This will delete all data)..."
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@make stop-graph-infrastructure
	container volume rm ninaivalaigal_graph_data ninaivalaigal_graph_redis_data 2>/dev/null || true
	@echo "✅ Graph data cleaned"

test-graph-all:
	@echo "🌐 Running all graph-related tests (SPEC-060 + SPEC-061 + API)..."
	@make test-graph && make test-graph-reasoner && make test-graph-intelligence-api
	@echo "✅ Complete graph testing suite finished"

spec-062:
	@echo "🎯 Running complete SPEC-062 GraphOps Stack validation..."
	@echo "📋 Validating GraphOps infrastructure..."
	@make check-graph-health
	@echo "🧪 Testing Apache AGE functionality..."
	@container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "SELECT name FROM ag_catalog.ag_graph WHERE name = 'ninaivalaigal_graph';" | grep -q "ninaivalaigal_graph" || (echo "❌ Graph not found" && exit 1)
	@echo "🔍 Testing Cypher queries..."
	@container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "LOAD 'age'; SET search_path = ag_catalog, \"\$$user\", public; SELECT * FROM cypher('ninaivalaigal_graph', \$$\$$ MATCH (u:User) RETURN count(u) \$$\$$) AS (count agtype);" > /dev/null || (echo "❌ Cypher queries failed" && exit 1)
	@echo "📊 Testing Redis cache..."
	@container exec ninaivalaigal-graph-redis redis-cli ping | grep -q "PONG" || (echo "❌ Redis not responding" && exit 1)
	@echo "🏗️ Testing dual-architecture builds..."
	@make build-graph-db-arm64 > /dev/null
	@echo "✅ SPEC-062 GraphOps Stack Deployment Architecture validation complete"

test-all:
	@echo "🧪 Running all test suites with coverage..."
	pytest --cov=server --cov-report=term --cov-report=html --cov-report=xml tests/

test-critical:
	@echo "🎯 Running critical module tests (auth, memory, rbac)..."
	pytest tests/ -k "auth or memory or rbac" -v --cov=server.auth --cov=server.memory --cov=server.rbac_middleware --cov-report=term

coverage-report:
	@echo "📊 Generating coverage report..."
	coverage report --show-missing

coverage-html:
	@echo "🌐 Generating HTML coverage report..."
	coverage html
	@echo "📊 Coverage report available at: htmlcov/index.html"

coverage-xml:
	@echo "📄 Generating XML coverage report..."
	coverage xml

coverage-dashboard:
	@echo "🎛️ Generating comprehensive coverage dashboard..."
	python coverage/generate_coverage_report.py
	@echo "🌐 Dashboard available at: coverage/dashboard.html"

validate-coverage:
	@echo "✅ Validating coverage requirements..."
	coverage report --fail-under=80

validate-critical-coverage:
	@echo "🎯 Validating critical module coverage (100% target)..."
	pytest --cov=server.auth --cov=server.memory --cov=server.rbac_middleware --cov-report=term --cov-fail-under=100 tests/ -k "auth or memory or rbac" || echo "⚠️ Critical modules need 100% coverage"

# Pre-commit hook management
pre-commit-enable:
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks enabled"

pre-commit-disable:
	@echo "🔧 Uninstalling pre-commit hooks..."
	pre-commit uninstall
	@echo "✅ Pre-commit hooks disabled"

pre-commit-update:
	@echo "🔄 Updating pre-commit hooks..."
	pre-commit clean
	pre-commit autoupdate

# Foundation SPEC Test targets
test-foundation:
	@echo "🧪 Running Foundation SPEC Tests..."
	pytest tests/foundation/ -v --cov=server --cov-report=html --cov-report=term

test-foundation-spec-007:
	@echo "🔍 Testing SPEC-007: Unified Context Scope System"
	pytest tests/foundation/spec_007/ -v

test-foundation-spec-012:
	@echo "💾 Testing SPEC-012: Memory Substrate"
	pytest tests/foundation/spec_012/ -v

test-foundation-spec-016:
	@echo "🔄 Testing SPEC-016: CI/CD Pipeline Architecture"
	pytest tests/foundation/spec_016/ -v

test-foundation-spec-020:
	@echo "🏗️ Testing SPEC-020: Memory Provider Architecture"
	pytest tests/foundation/spec_020/ -v

test-foundation-spec-049:
	@echo "🤝 Testing SPEC-049: Memory Sharing Collaboration"
	pytest tests/foundation/spec_049/ -v

test-foundation-spec-052:
	@echo "📊 Testing SPEC-052: Comprehensive Test Coverage"
	pytest tests/foundation/spec_052/ -v

test-foundation-spec-058:
	@echo "📚 Testing SPEC-058: Documentation Expansion"
	pytest tests/foundation/spec_058/ -v

test-foundation-spec-060:
	@echo "🔗 Testing SPEC-060: Unification"
	pytest tests/foundation/spec_060/ -v

test-foundation-spec-061:
	@echo "⚡ Testing SPEC-061: Advanced Execution"
	pytest tests/foundation/spec_061/ -v

test-foundation-spec-062:
	@echo "🏗️ Testing SPEC-062: GraphOps Deployment"
	pytest tests/foundation/spec_062/ -v

test-foundation-spec-063:
	@echo "🤖 Testing SPEC-063: Agentic Core"
	pytest tests/foundation/spec_063/ -v

# Phase 2B: Unified Integration Tests
test-spec-040-062-unified:
	@echo "🔗 Testing SPEC-040 + SPEC-062 Unified Integration"
	pytest tests/integration/spec_040_062_unified/ -v

# CI Recovery and Self-Heal
test-ci-recovery:
	@echo "🛡️ Testing CI Recovery System"
	python3 scripts/ci-recovery.py --test-mode

validate-phase-2b:
	@echo "✅ Validating Phase 2B Implementation"
	@echo "📊 Checking unified testbed structure..."
	@test -f tests/integration/spec_040_062_unified/test_memory_graph_unified.py && echo "✅ Unified testbed present" || echo "❌ Missing unified testbed"
	@echo "🔧 Validating CI recovery system..."
	@test -f scripts/ci-recovery.py && echo "✅ CI recovery system present" || echo "❌ Missing CI recovery system"
	@test -f scripts/post-failure-hook.sh && echo "✅ Post-failure hook present" || echo "❌ Missing post-failure hook"
	@echo "📋 Checking configuration..."
	@test -f .env.monitoring && echo "✅ Monitoring configuration present" || echo "❌ Missing .env.monitoring"
	@test -f .github/workflows/healthcheck-restart.yml && echo "✅ HealthCheck workflow present" || echo "❌ Missing healthcheck workflow"
	@test -f phase-2b-validation.md && echo "✅ Phase 2B validation report present" || echo "❌ Missing validation report"
	@echo "🎉 Phase 2B validation complete!"

# Phase 3: GitOps + Kubernetes Deployment (SPEC-021)
validate-k8s-manifests:
	@echo "🔍 Validating Kubernetes manifests..."
	@test -d k8s/base && echo "✅ Base manifests present" || echo "❌ Missing base manifests"
	@test -d k8s/overlays && echo "✅ Environment overlays present" || echo "❌ Missing overlays"
	@test -d k8s/argocd && echo "✅ ArgoCD configuration present" || echo "❌ Missing ArgoCD config"
	@test -f k8s/README.md && echo "✅ K8s documentation present" || echo "❌ Missing K8s docs"

setup-argocd:
	@echo "🚀 Setting up ArgoCD for GitOps..."
	./scripts/setup-argocd.sh

deploy-dev:
	@echo "🏗️ Deploying to development environment..."
	kubectl apply -k k8s/overlays/dev/

deploy-staging:
	@echo "🎯 Deploying to staging environment..."
	kubectl apply -k k8s/overlays/staging/

build-container:
	@echo "🐳 Building container image..."
	docker build -t ninaivalaigal/api-server:latest .

push-container:
	@echo "📤 Pushing container to registry..."
	docker push ninaivalaigal/api-server:latest

validate-spec-021:
	@echo "✅ Validating SPEC-021: GitOps + Kubernetes Deployment"
	@echo "📊 Checking Kubernetes manifests..."
	make validate-k8s-manifests
	@echo "🔧 Validating GitOps workflow..."
	@test -f .github/workflows/gitops-deployment.yml && echo "✅ GitOps workflow present" || echo "❌ Missing GitOps workflow"
	@test -f scripts/setup-argocd.sh && echo "✅ ArgoCD setup script present" || echo "❌ Missing ArgoCD setup"
	@echo "🎉 SPEC-021 validation complete!"

# Foundation test monitoring and validation
check-env:
	@echo "🔍 Validating Foundation test environment..."
	./scripts/check-env.sh

test-foundation-performance:
	@echo "⚡ Running Foundation performance benchmarks..."
	pytest tests/foundation/ -k "performance" --benchmark-only -v

test-foundation-chaos:
	@echo "💥 Running Foundation chaos tests..."
	pytest tests/foundation/ -k "chaos" -v

test-foundation-coverage:
	@echo "📈 Generating Foundation coverage report..."
	pytest tests/foundation/ --cov=server --cov-report=html --cov-report=xml --cov-fail-under=85

# Foundation test reporting
foundation-report:
	@echo "📊 Generating Foundation test report..."
	pytest tests/foundation/ --cov=server --cov-report=html --html=reports/foundation-test-report.html --self-contained-html

# Foundation test cleanup
clean-foundation-reports:
	@echo "🧹 Cleaning Foundation test reports..."
	rm -rf htmlcov/
	rm -rf reports/
	rm -f coverage.xml
	rm -f .coverage
	@echo "✅ Pre-commit hooks updated"

pre-commit-run:
	@echo "🧪 Running pre-commit on all files..."
	pre-commit run --all-files

pre-commit-fix:
	@echo "🔧 Running pre-commit with auto-fixes..."
	pre-commit run --all-files || true
	@echo "✅ Pre-commit fixes applied"

# Environment setup
setup-env:
	@echo "🔧 Setting up environment..."
	./scripts/setup-env.sh
	@echo "✅ Environment setup complete"

# Security cleanup
security-cleanup:
	@echo "🔒 Running security cleanup..."
	@echo "Removing config files with secrets from git tracking..."
	git rm --cached *.config.json 2>/dev/null || true
	@echo "✅ Security cleanup complete"

# Development stack management
dev-up:
	@echo "🚀 Starting full development stack..."
	./scripts/bring-up-dev.sh

dev-down:
	@echo "🛑 Stopping development stack..."
	@make stop-graph-infrastructure || true
	@./scripts/nv-stack-stop.sh || true
	@echo "✅ Development stack stopped"

dev-status:
	@echo "📊 Development stack status..."
	@container list | grep -E "(nv-|ninaivalaigal-)" || echo "No development containers running"

# =============================================================================
# SPEC-056: Dependency & Testing Improvements
# =============================================================================

## Compile requirements files using pip-tools
deps-compile:
	@echo "🔧 Compiling requirements files..."
	@$(SCRIPTS)/manage-deps.sh compile all

## Install development dependencies
deps-install-dev:
	@echo "📦 Installing development dependencies..."
	@$(SCRIPTS)/manage-deps.sh install dev

## Install production dependencies
deps-install-prod:
	@echo "📦 Installing production dependencies..."
	@$(SCRIPTS)/manage-deps.sh install base

## Install test dependencies
deps-install-test:
	@echo "📦 Installing test dependencies..."
	@$(SCRIPTS)/manage-deps.sh install test

## Update all dependencies to latest versions
deps-update:
	@echo "⬆️ Updating all dependencies..."
	@$(SCRIPTS)/manage-deps.sh update

## Check for dependency conflicts
deps-check:
	@echo "🔍 Checking for dependency conflicts..."
	@$(SCRIPTS)/manage-deps.sh check

## Show dependency tree
deps-tree:
	@echo "🌳 Showing dependency tree..."
	@$(SCRIPTS)/manage-deps.sh tree

## Clean up old requirements files
deps-cleanup:
	@echo "🧹 Cleaning up old requirements files..."
	@$(SCRIPTS)/manage-deps.sh cleanup

## Run tests with improved mocks and fixtures
test-with-mocks:
	@echo "🧪 Running tests with comprehensive mocks..."
	@python -m pytest tests/unit/test_memory_with_mocks.py -v

## Run all unit tests with mocks
test-unit-mocked:
	@echo "🧪 Running all unit tests with mocks..."
	@python -m pytest tests/unit/ -v --tb=short

## Run performance tests with benchmarks
test-performance:
	@echo "⚡ Running performance tests..."
	@python -m pytest tests/performance/ -v --benchmark-only

## Validate test fixtures and mocks
test-fixtures:
	@echo "🔧 Validating test fixtures..."
	@python -c "from tests.fixtures import *; print('✅ All fixtures imported successfully')"

# =============================================================================
# SPEC-054: Secret Management Commands
# =============================================================================

## Setup secure environment configuration
secrets-setup:
	@echo "🔒 Setting up secure environment..."
	@$(SCRIPTS)/setup-secrets.sh --all

## Scan for hardcoded secrets
secrets-scan:
	@echo "🔍 Scanning for hardcoded secrets..."
	@$(SCRIPTS)/setup-secrets.sh --scan

## Create .env file with secure passwords
secrets-create-env:
	@echo "🔑 Creating secure .env file..."
	@$(SCRIPTS)/setup-secrets.sh --create-env

## Validate environment configuration
secrets-validate:
	@echo "✅ Validating environment configuration..."
	@$(SCRIPTS)/setup-secrets.sh --validate

# =============================================================================
# Automation Management
# =============================================================================

## Start all automation (health monitor + graph tests + container guard)
automation-start:
	@echo "🚀 Starting Ninaivalaigal Automation Suite..."
	@cp scripts/automation/com.ninaivalaigal.health-monitor.plist ~/Library/LaunchAgents/ 2>/dev/null || cp /Users/swami/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist ~/Library/LaunchAgents/
	@cp scripts/automation/com.ninaivalaigal.graph-test.plist ~/Library/LaunchAgents/
	@launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist
	@launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.graph-test.plist
	@nohup ./.guard-docker.sh monitor > /tmp/container-guard-monitor.log 2>&1 & echo $$! > /tmp/guard-docker.pid
	@echo "✅ Automation started - check status with 'make automation-status'"

## Stop all automation
automation-stop:
	@echo "🛑 Stopping Ninaivalaigal Automation..."
	@launchctl unload ~/Library/LaunchAgents/com.ninaivalaigal.health-monitor.plist 2>/dev/null || true
	@launchctl unload ~/Library/LaunchAgents/com.ninaivalaigal.graph-test.plist 2>/dev/null || true
	@pkill -f "guard-docker.sh" || true
	@rm -f /tmp/guard-docker.pid
	@echo "✅ Automation stopped"

## Check automation status
automation-status:
	@echo "📊 Ninaivalaigal Automation Status"
	@echo "=================================="
	@echo "Health Monitor:"
	@launchctl list com.ninaivalaigal.health-monitor 2>/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo "Graph Tests:"
	@launchctl list com.ninaivalaigal.graph-test 2>/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo "Container Guard:"
	@pgrep -f "guard-docker.sh" >/dev/null && echo "  ✅ Running (PID: $$(pgrep -f guard-docker.sh))" || echo "  ❌ Not running"
	@echo "Container Protection:"
	@./.guard-docker.sh status 2>/dev/null || echo "  ⚠️  Guard not available"

## Show recent automation logs
automation-logs:
	@echo "📋 Recent Health Monitor Logs:"
	@tail -10 /tmp/ninaivalaigal-health-fixed.log 2>/dev/null || echo "No health logs found"
	@echo ""
	@echo "📋 Recent Graph Test Logs:"
	@tail -10 /tmp/graph-test.log 2>/dev/null || echo "No graph test logs found"
	@echo ""
	@echo "📋 Recent Container Guard Logs:"
	@tail -10 /tmp/container-guard.log 2>/dev/null || echo "No guard logs found"

## Fix Redis ping() usage in graph intelligence
fix-redis:
	@echo "🔧 Fixing Redis ping() usage..."
	@python scripts/fix-redis-ping.py
	@echo "✅ Redis fix completed"

## Run graph intelligence validation once
test-graph:
	@echo "🧠 Testing Graph Intelligence..."
	@conda run -n nina python /Users/swami/Downloads/simple_enhanced_graph_test.py

## Emergency restart with automation protection
emergency-restart:
	@echo "🚨 Emergency restart requested..."
	@make automation-stop
	@make stack-down || true
	@sleep 10
	@make stack-up
	@make automation-start
	@echo "✅ Emergency restart completed with automation restored"

## ========================================
## NINA INTELLIGENCE STACK (CONSOLIDATED)
## ========================================

## start nina intelligence stack: nina-intelligence-db + nina-intelligence-cache + API
nina-stack-up:
	@$(SCRIPTS)/nina-intelligence-stack-start.sh

## stop nina intelligence stack
nina-stack-down:
	@$(SCRIPTS)/nina-intelligence-stack-stop.sh

## show nina intelligence stack status
nina-stack-status:
	@$(SCRIPTS)/nina-intelligence-stack-status.sh

## start only nina-intelligence-db (PostgreSQL + Apache AGE + pgvector)
nina-db-only:
	@$(SCRIPTS)/nina-intelligence-stack-start.sh --db-only

## start stack without cache
nina-no-cache:
	@$(SCRIPTS)/nina-intelligence-stack-start.sh --skip-cache

## start stack without API
nina-no-api:
	@$(SCRIPTS)/nina-intelligence-stack-start.sh --skip-api

## start nina intelligence health monitoring
nina-health-start:
	@cp $(SCRIPTS)/automation/com.ninaivalaigal.nina-intelligence-health.plist ~/Library/LaunchAgents/
	@launchctl load ~/Library/LaunchAgents/com.ninaivalaigal.nina-intelligence-health.plist
	@echo "✅ Nina Intelligence Health Monitor started"

## stop nina intelligence health monitoring
nina-health-stop:
	@launchctl unload ~/Library/LaunchAgents/com.ninaivalaigal.nina-intelligence-health.plist 2>/dev/null || true
	@echo "🛑 Nina Intelligence Health Monitor stopped"

## check nina intelligence health status
nina-health-check:
	@$(SCRIPTS)/nina-intelligence-health-monitor.sh check

## view nina intelligence health logs
nina-health-logs:
	@tail -20 /tmp/nina-intelligence-health.log

## open nina intelligence UI in browser
nina-ui-open:
	@echo "🌐 Opening Nina Intelligence UI..."
	@open http://localhost:8081
