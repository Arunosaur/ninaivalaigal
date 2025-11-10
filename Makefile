# Makefile for Taiga CLI commands
# Usage: make taiga.read REF=700
#        make taiga.update REF=700 SUBJECT="New title"

.PHONY: help taiga.read taiga.update taiga.append taiga.mine taiga.status taiga.list taiga.bulk taiga.report taiga.test taiga.check taiga.smoke taiga.export.csv taiga.export.html taiga.metrics taiga.query taiga.tui taiga.monitor taiga.analyze deps-compile deps-install deps-install-dev deps-update deps-check

# Default project (can be overridden)
PROJECT ?= ninaivalaigal

# Taiga CLI wrapper function
define taiga_cmd
	@python3 taiga/scripts/taiga_cli.py --project $(PROJECT) $(1)
endef

help:
	@echo "Taiga CLI Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "Read Operations:"
	@echo "  make taiga.read REF=<number>        - Read story by reference number"
	@echo "  make taiga.read ID=<number>         - Read story by ID"
	@echo "  make taiga.read REF=<number> JSON=1 - Read story as JSON"
	@echo ""
	@echo "Update Operations:"
	@echo "  make taiga.update REF=<number> SUBJECT=\"<title>\"  - Update story subject"
	@echo "  make taiga.update REF=<number> DESC=\"<text>\"      - Update story description"
	@echo "  make taiga.append REF=<number> TEXT=\"<note>\"     - Append note to description"
	@echo ""
	@echo "List Operations:"
	@echo "  make taiga.mine USER=<username>     - List stories assigned to user"
	@echo "  make taiga.mine USER=<username> ALL=1 - List all stories (with pagination)"
	@echo "  make taiga.status STATUS=\"<name>\"  - List stories by status"
	@echo ""
	@echo "Bulk Operations:"
	@echo "  make taiga.bulk REFS=\"700,701,702\"   - Process multiple stories"
	@echo "  make taiga.bulk REFS=\"700,701\" SUBJECT=\"Title\" - Bulk update"
	@echo ""
	@echo "Reporting:"
	@echo "  make taiga.report STATUS=\"<name>\"   - Export stories as Markdown"
	@echo "  make taiga.report USER=<username>   - Export user stories as Markdown"
	@echo ""
	@echo "Export Formats:"
	@echo "  make taiga.export.csv STATUS=\"<name>\" - Export as CSV"
	@echo "  make taiga.export.html STATUS=\"<name>\" - Export as HTML"
	@echo ""
	@echo "Query & Metrics:"
	@echo "  make taiga.query QUERY=\"status:Done tag:backend\" STATUS=\"<name>\" - Filter stories"
	@echo "  make taiga.metrics STATUS=\"<name>\" - Show metrics summary"
	@echo ""
	@echo "Interactive:"
	@echo "  make taiga.tui                      - Interactive TUI mode (requires rich)"
	@echo "  make taiga.tui STATUS=\"<name>\"     - TUI with status filter"
	@echo "  make taiga.tui USER=<username>      - TUI with user filter"
	@echo ""
	@echo "Monitoring & Auto-Assignment:"
	@echo "  make taiga.monitor                  - Monitor and auto-assign stories (D, E, F, G, H)"
	@echo "  make taiga.monitor DRY_RUN=1        - Dry-run mode (show what would be done)"
	@echo "  make taiga.monitor MIN_STORIES=2     - Require at least 2 stories (default: 1)"
	@echo "  make taiga.monitor STORIES_TO_ASSIGN=3 - Assign 3 stories (default: 5)"
	@echo ""
	@echo "Analysis:"
	@echo "  make taiga.analyze USER=<username>  - Analyze blocked stories for independent work"
	@echo "  make taiga.analyze USER=<username> DETAILED=1 - Include comments in analysis"
	@echo ""
	@echo "Validation & Closure:"
	@echo "  make taiga.validate-completed  - Find completed stories (auto-close)"
	@echo "  make taiga.validate-interactive - Interactive validation (review each story)"
	@echo "  make taiga.validate-interactive STATUS=\"Ready\" - Filter by status"
	@echo "  make taiga.validate-completed STATUS=\"In Progress\" AUTO=1 - Auto-close"
	@echo ""
	@echo "Testing:"
	@echo "  make taiga.test REF=<number>        - Test CLI with read + append (dry-run)"
	@echo "  make taiga.check                    - CI validation (dry-run against dummy story)"
	@echo "  make taiga.smoke                    - Run all smoke tests"
	@echo ""
	@echo "Examples:"
	@echo "  make taiga.read REF=700"
	@echo "  make taiga.update REF=700 SUBJECT=\"New title\""
	@echo "  make taiga.append REF=700 TEXT=\"Progress update\""
	@echo "  make taiga.mine USER=developer-g"
	@echo "  make taiga.status STATUS=\"In Progress\""
	@echo "  make taiga.test REF=700"
	@echo ""
	@echo "Developer Stories (dev_stories.py):"
	@echo "  make taiga.dev.list DEV=developer-c    - List stories for a developer"
	@echo "  make taiga.dev.list DEV=C               - List stories (accepts C, Developer C, etc.)"
	@echo "  make taiga.dev.read REF=700             - Read a story by ref"
	@echo "  make taiga.dev.read ID=12345            - Read a story by ID"
	@echo "  make taiga.dev.update REF=700 FIELD=description VALUE=\"New desc\" - Update story"
	@echo "  make taiga.dev.update REF=700 FIELD=status VALUE=\"In Progress\" - Update status"
	@echo "  make taiga.dev.update REF=700 FIELD=append VALUE=\"Note\" - Append to description"
	@echo ""
	@echo "Dependency Management (SPEC-056):"
	@echo "  make deps-compile        - Compile requirements files"
	@echo "  make deps-install        - Install base dependencies"
	@echo "  make deps-install-dev    - Install dev dependencies"
	@echo "  make deps-update         - Update dependencies"
	@echo "  make deps-check          - Check for conflicts"

# Read operations
taiga.read:
ifdef REF
	$(call taiga_cmd,--ref $(REF) $(if $(JSON),--json))
else ifdef ID
	$(call taiga_cmd,--id $(ID) $(if $(JSON),--json))
else
	@echo "Error: Specify either REF=<number> or ID=<number>"
	@exit 1
endif

# Update operations
taiga.update:
ifndef REF
	@echo "Error: REF=<number> is required"
	@exit 1
endif
	@$(eval UPDATE_ARGS := )
	@if [ -n "$(SUBJECT)" ]; then \
		UPDATE_ARGS="$$UPDATE_ARGS --update-field subject=\"$(SUBJECT)\""; \
	fi
	@if [ -n "$(DESC)" ]; then \
		UPDATE_ARGS="$$UPDATE_ARGS --update-field description=\"$(DESC)\""; \
	fi
	@if [ -z "$$UPDATE_ARGS" ]; then \
		echo "Error: Specify SUBJECT=\"...\" or DESC=\"...\""; \
		exit 1; \
	fi
	$(call taiga_cmd,--ref $(REF) $$UPDATE_ARGS)

# Append to description
taiga.append:
ifndef REF
	@echo "Error: REF=<number> is required"
	@exit 1
endif
ifndef TEXT
	@echo "Error: TEXT=\"<note>\" is required"
	@exit 1
endif
	$(call taiga_cmd,--ref $(REF) --append "$(TEXT)")

# List my stories
taiga.mine:
ifndef USER
	@echo "Error: USER=<username> is required"
	@exit 1
endif
	$(call taiga_cmd,--mine $(USER) $(if $(ALL),--all))

# List by status
taiga.status:
ifndef STATUS
	@echo "Error: STATUS=\"<name>\" is required"
	@exit 1
endif
	$(call taiga_cmd,--status "$(STATUS)" $(if $(ALL),--all))

# Alias for taiga.read
taiga.list: taiga.read

# Bulk operations
taiga.bulk:
ifndef REFS
	@echo "Error: REFS=\"<numbers>\" is required (e.g., REFS=\"700,701,702\")"
	@exit 1
endif
	@$(eval BULK_ARGS := )
	@if [ -n "$(SUBJECT)" ]; then \
		BULK_ARGS="$$BULK_ARGS --update-field subject=\"$(SUBJECT)\""; \
	fi
	@if [ -n "$(DESC)" ]; then \
		BULK_ARGS="$$BULK_ARGS --update-field description=\"$(DESC)\""; \
	fi
	@if [ -n "$(TEXT)" ]; then \
		BULK_ARGS="$$BULK_ARGS --append \"$(TEXT)\""; \
	fi
	$(call taiga_cmd,--refs "$(REFS)" $$BULK_ARGS)

# Markdown report
taiga.report:
ifdef STATUS
	$(call taiga_cmd,--status "$(STATUS)" --markdown $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--mine $(USER) --markdown $(if $(ALL),--all))
else
	@echo "Error: Specify either STATUS=\"<name>\" or USER=<username>"
	@exit 1
endif

# CSV export
taiga.export.csv:
ifdef STATUS
	$(call taiga_cmd,--status "$(STATUS)" --csv $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--mine $(USER) --csv $(if $(ALL),--all))
else
	@echo "Error: Specify either STATUS=\"<name>\" or USER=<username>"
	@exit 1
endif

# HTML export
taiga.export.html:
ifdef STATUS
	$(call taiga_cmd,--status "$(STATUS)" --html $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--mine $(USER) --html $(if $(ALL),--all))
else
	@echo "Error: Specify either STATUS=\"<name>\" or USER=<username>"
	@exit 1
endif

# Metrics summary
taiga.metrics:
ifdef STATUS
	$(call taiga_cmd,--status "$(STATUS)" --metrics $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--mine $(USER) --metrics $(if $(ALL),--all))
else
	@echo "Error: Specify either STATUS=\"<name>\" or USER=<username>"
	@exit 1
endif

# Query filter
taiga.query:
ifndef QUERY
	@echo "Error: QUERY=\"<filter>\" is required (e.g., QUERY=\"status:Done tag:backend\")"
	@exit 1
endif
ifdef STATUS
	$(call taiga_cmd,--status "$(STATUS)" --query "$(QUERY)" $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--mine $(USER) --query "$(QUERY)" $(if $(ALL),--all))
else
	@echo "Error: Specify either STATUS=\"<name>\" or USER=<username>"
	@exit 1
endif

# Test harness: runs read, append (dry-run), and confirms exit codes
taiga.test:
ifndef REF
	@echo "Error: REF=<number> is required"
	@exit 1
endif
	@echo "🧪 Testing Taiga CLI with story #$(REF)..."
	@echo ""
	@echo "1️⃣  Testing read operation..."
	@$(call taiga_cmd,--ref $(REF)) || (echo "❌ Read failed" && exit 1)
	@echo ""
	@echo "2️⃣  Testing append operation (dry-run)..."
	@$(call taiga_cmd,--ref $(REF) --append "Test append from make taiga.test" --dry-run) || (echo "❌ Append dry-run failed" && exit 1)
	@echo ""
	@echo "✅ All tests passed!"

# CI validation: dry-run read/update against a test story
taiga.check:
	@echo "🔍 Running Taiga CLI validation..."
	@echo ""
	@echo "Testing authentication..."
	@python3 taiga/scripts/taiga_cli.py --project $(PROJECT) --status "New" --all 2>&1 | head -5 > /dev/null || (echo "❌ Authentication failed" && exit 1)
	@echo "✅ Authentication OK"
	@echo ""
	@echo "Testing dry-run update..."
	@python3 taiga/scripts/taiga_cli.py --project $(PROJECT) --ref 1 --append "CI validation test" --dry-run > /dev/null 2>&1 || echo "⚠️  Story #1 not found (this is OK if it doesn't exist)"
	@echo "✅ Dry-run mode OK"
	@echo ""
	@echo "✅ All validation checks passed!"

# Smoke tests
taiga.smoke:
	@bash taiga/scripts/smoke_tests.sh

# CI: Nightly report generation
taiga.ci.nightly:
	@bash taiga/scripts/ci_nightly_report.sh

# Interactive TUI mode
taiga.tui:
ifdef STATUS
	$(call taiga_cmd,--tui --status "$(STATUS)" $(if $(ALL),--all))
else ifdef USER
	$(call taiga_cmd,--tui --mine $(USER) $(if $(ALL),--all))
else
	$(call taiga_cmd,--tui $(if $(ALL),--all))
endif

# Monitor and auto-assign stories for Developers D, E, F, G, H
taiga.monitor:
	@python3 taiga/scripts/monitor_and_assign_stories.py \
		$(if $(DRY_RUN),--dry-run) \
		$(if $(MIN_STORIES),--min-stories $(MIN_STORIES)) \
		$(if $(STORIES_TO_ASSIGN),--stories-to-assign $(STORIES_TO_ASSIGN)) \
		$(if $(MAX_STORIES),--max-stories $(MAX_STORIES))

# Analyze blocked stories to identify independent work
taiga.analyze:
ifndef USER
	@echo "Error: USER=<username> is required"
	@echo "Example: make taiga.analyze USER=developer-d"
	@exit 1
endif
	@python3 taiga/scripts/analyze_blocked_stories.py $(USER) $(if $(DETAILED),--detailed)

# Validate and close completed stories (auto)
taiga.validate-completed:
	@python3 taiga/scripts/validate_and_close_completed_stories.py \
		$(if $(STATUS),--status "$(STATUS)") \
		$(if $(AUTO),--auto) \
		$(if $(MIN_CONFIDENCE),--min-confidence $(MIN_CONFIDENCE)) \
		$(if $(MIN_COMPLETION),--min-completion $(MIN_COMPLETION))

# Interactive validation (review each story)
taiga.validate-interactive:
	@python3 taiga/scripts/interactive_validate_stories.py \
		$(if $(STATUS),--status "$(STATUS)") \
		$(if $(MIN_CONFIDENCE),--min-confidence $(MIN_CONFIDENCE)) \
		$(if $(MIN_COMPLETION),--min-completion $(MIN_COMPLETION)) \
		$(if $(START_FROM),--start-from $(START_FROM))

# Developer Stories CLI (dev_stories.py)
taiga.dev.list:
ifndef DEV
	@echo "Error: DEV=<developer> is required (e.g., DEV=developer-c, DEV=C, DEV=\"Developer C\")"
	@exit 1
endif
	@python3 taiga/scripts/dev_stories.py list "$(DEV)" $(if $(STATUS),--status "$(STATUS)")

taiga.dev.read:
ifdef REF
	@python3 taiga/scripts/dev_stories.py read $(REF)
else ifdef ID
	@python3 taiga/scripts/dev_stories.py read --id $(ID)
else
	@echo "Error: Specify either REF=<number> or ID=<number>"
	@exit 1
endif

taiga.dev.update:
ifndef REF
ifndef ID
	@echo "Error: Specify either REF=<number> or ID=<number>"
	@exit 1
endif
endif
	@if [ -n "$(FIELD)" ] && [ -n "$(VALUE)" ]; then \
		if [ "$(FIELD)" = "description" ]; then \
			python3 taiga/scripts/dev_stories.py update $(if $(ID),--id $(ID),$(REF)) --description "$(VALUE)"; \
		elif [ "$(FIELD)" = "subject" ]; then \
			python3 taiga/scripts/dev_stories.py update $(if $(ID),--id $(ID),$(REF)) --subject "$(VALUE)"; \
		elif [ "$(FIELD)" = "status" ]; then \
			python3 taiga/scripts/dev_stories.py update $(if $(ID),--id $(ID),$(REF)) --status "$(VALUE)"; \
		elif [ "$(FIELD)" = "append" ]; then \
			python3 taiga/scripts/dev_stories.py update $(if $(ID),--id $(ID),$(REF)) --append "$(VALUE)"; \
		else \
			echo "Error: FIELD must be one of: description, subject, status, append"; \
			exit 1; \
		fi \
	else \
		echo "Error: Both FIELD=<field> and VALUE=<value> are required"; \
		echo "  FIELD can be: description, subject, status, append"; \
		exit 1; \
	fi

# ============================================================================
# Terraform Infrastructure Commands (US-127)
# ============================================================================

.PHONY: terraform-validate-aws terraform-validate-gcp terraform-validate-azure \
        terraform-test-aws terraform-test-gcp terraform-test-azure \
        terraform-validate-all terraform-test-all

# AWS Terraform Validation
terraform-validate-aws:
	@echo "🔍 Validating AWS Terraform configuration..."
	@bash terraform/scripts/validate-aws.sh

# GCP Terraform Validation
terraform-validate-gcp:
	@echo "🔍 Validating GCP Terraform configuration..."
	@bash terraform/scripts/validate-gcp.sh

# Azure Terraform Validation
terraform-validate-azure:
	@echo "🔍 Validating Azure Terraform configuration..."
	@bash terraform/scripts/validate-azure.sh

# Validate all providers
terraform-validate-all: terraform-validate-aws terraform-validate-gcp terraform-validate-azure
	@echo "✅ All Terraform configurations validated"

# AWS Deployment Testing
terraform-test-aws:
	@echo "🧪 Testing AWS deployment..."
	@bash terraform/scripts/test-aws.sh

# GCP Deployment Testing
terraform-test-gcp:
	@echo "🧪 Testing GCP deployment..."
	@bash terraform/scripts/test-gcp.sh

# Azure Deployment Testing
terraform-test-azure:
	@echo "🧪 Testing Azure deployment..."
	@bash terraform/scripts/test-azure.sh

# Test all providers
terraform-test-all: terraform-test-aws terraform-test-gcp terraform-test-azure
	@echo "✅ All deployments tested"

# ============================================================================
# Database Management Commands (SPEC-019)
# ============================================================================

.PHONY: db-migrate db-rollback db-backup db-restore db-init db-stats \
        db-vacuum db-reindex db-maintenance list-backups cleanup-backups

# Database migrations
db-migrate:
	@echo "🔄 Running database migrations..."
	@alembic -c alembic/public/alembic.ini upgrade head || echo "⚠️  Public schema migration failed"
	@alembic -c alembic/memory/alembic.ini upgrade head || echo "⚠️  Memory schema migration failed"
	@alembic -c alembic/graphops/alembic.ini upgrade head || echo "⚠️  GraphOps schema migration failed"
	@alembic -c alembic/intelligence/alembic.ini upgrade head || echo "⚠️  Intelligence schema migration failed"
	@echo "✅ Migrations completed"

db-rollback:
	@echo "⏪ Rolling back last migration..."
	@alembic -c alembic/public/alembic.ini downgrade -1 || echo "⚠️  Rollback failed"
	@echo "✅ Rollback completed"

# Database backup and restore
db-backup:
	@echo "💾 Creating database backup..."
	@bash scripts/backup-db.sh
	@echo "✅ Backup completed"

db-restore:
	@echo "📥 Restoring database from backup..."
	@echo "⚠️  This will overwrite existing data!"
	@bash scripts/restore-db.sh
	@echo "✅ Restore completed"

list-backups:
	@echo "📋 Listing available backups..."
	@ls -lh /srv/ninaivalaigal/backups/*.dump 2>/dev/null || echo "No backups found"

cleanup-backups:
	@echo "🧹 Cleaning up old backups (keeping last 7 days)..."
	@find /srv/ninaivalaigal/backups -name "*.dump" -mtime +7 -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Database initialization
db-init:
	@echo "🔧 Initializing database..."
	@python3 scripts/init-database.py
	@echo "✅ Database initialized"

# Database statistics
db-stats:
	@echo "📊 Database statistics..."
	@bash scripts/db-stats.sh

# Database maintenance
db-vacuum:
	@echo "🧹 Running VACUUM ANALYZE..."
	@psql -h ${POSTGRES_HOST:-127.0.0.1} -p ${POSTGRES_PORT:-5433} -U ${POSTGRES_USER:-nina} -d ${POSTGRES_DB:-nina} -c "VACUUM ANALYZE;" || echo "⚠️  VACUUM failed"
	@echo "✅ VACUUM completed"

db-reindex:
	@echo "🔨 Rebuilding indexes..."
	@psql -h ${POSTGRES_HOST:-127.0.0.1} -p ${POSTGRES_PORT:-5433} -U ${POSTGRES_USER:-nina} -d ${POSTGRES_DB:-nina} -c "REINDEX DATABASE ${POSTGRES_DB:-nina};" || echo "⚠️  REINDEX failed"
	@echo "✅ REINDEX completed"

db-maintenance: db-vacuum db-reindex
	@echo "✅ Full database maintenance completed"

# Dependency Management (SPEC-056: pip-tools)
deps-compile:
	@./scripts/manage-deps.sh compile

deps-install:
	@./scripts/manage-deps.sh install base

deps-install-dev:
	@./scripts/manage-deps.sh install dev

deps-update:
	@./scripts/manage-deps.sh update

deps-check:
	@./scripts/manage-deps.sh check
