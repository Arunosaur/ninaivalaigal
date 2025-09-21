# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb skip-mem0 with-mem0 with-ui logs backup db-stats pgb-stats restore verify-backup verify-latest cleanup-backups cleanup-backups-dry spec-new spec-test system-info test-mem0-auth ui-up ui-down ui-status sanity-check validate-production start stop health metrics dev-up dev-down dev-logs dev-status tunnel-start tunnel-stop deploy-aws-vm deploy-gcp-vm deploy-azure-vm deploy-aws deploy-gcp deploy-azure k8s-deploy k8s-status k8s-logs k8s-delete build-images install uninstall ci-test release release-local

## start full stack: DB → PgBouncer → Mem0 → API → UI
stack-up:
	@$(SCRIPTS)/nv-stack-start.sh

## stop stack: UI → API → Mem0 → PgBouncer → DB
stack-down:
	@$(SCRIPTS)/nv-stack-stop.sh

## show status of all 5 services
stack-status:
	@$(SCRIPTS)/nv-stack-status.sh

## bring up only the database
db-only:
	@$(SCRIPTS)/nv-stack-start.sh --db-only

## bring up DB + PgBouncer but skip Mem0 and API
skip-api:
	@$(SCRIPTS)/nv-stack-start.sh --skip-api

## bring up DB + API but skip PgBouncer
skip-pgb:
	@$(SCRIPTS)/nv-stack-start.sh --skip-pgb

## bring up DB + PgBouncer + API but skip Mem0
skip-mem0:
	@$(SCRIPTS)/nv-stack-start.sh --skip-mem0

## bring up DB + PgBouncer + Mem0 but skip API
with-mem0:
	@$(SCRIPTS)/nv-stack-start.sh --with-mem0 --skip-api

## bring up full stack with UI
with-ui:
	@$(SCRIPTS)/nv-stack-start.sh --with-ui

## tail logs for all containers
logs:
	@echo "== DB logs ==";        -container logs -f nv-db & \
	 echo "== PgBouncer logs =="; -container logs -f nv-pgbouncer & \
	 echo "== Mem0 logs ==";      -container logs -f nv-mem0 & \
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

## test mem0 sidecar authentication
test-mem0-auth:
	@$(SCRIPTS)/test-mem0-auth.sh

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
	@$(SCRIPTS)/nv-stack-start.sh --skip-mem0
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
		-t $(IMAGE_NAME)-api:local-test \
		-f Dockerfile.api .
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
