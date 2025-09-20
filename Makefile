# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb skip-mem0 with-mem0 with-ui logs backup db-stats pgb-stats restore verify-backup verify-latest cleanup-backups cleanup-backups-dry spec-new spec-test system-info test-mem0-auth ui-up ui-down ui-status sanity-check validate-production start stop health metrics dev-up dev-down dev-logs dev-status tunnel-start tunnel-stop deploy-aws deploy-gcp deploy-azure build-images install uninstall ci-test release release-local

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

health:
	@echo "🏥 Health Check Summary"
	@echo "======================"
	@curl -s http://localhost:13370/health | jq .
	@echo ""
	@curl -s http://localhost:13370/health/detailed | jq .
	@echo ""
	@curl -s http://localhost:13370/memory/health | jq .

metrics:
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

deploy-aws:
	@echo "🚀 Deploying to AWS..."
	@echo "Usage: KEY_NAME=my-key make deploy-aws"
	@$(SCRIPTS)/deploy-aws.sh

deploy-gcp:
	@echo "🚀 Deploying to Google Cloud Platform..."
	@echo "Usage: PROJECT_ID=my-project make deploy-gcp"
	@$(SCRIPTS)/deploy-gcp.sh

deploy-azure:
	@echo "🚀 Deploying to Microsoft Azure..."
	@echo "Usage: RESOURCE_GROUP=my-rg make deploy-azure"
	@$(SCRIPTS)/deploy-azure.sh

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
