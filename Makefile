# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb skip-mem0 with-mem0 with-ui logs backup db-stats restore spec-new spec-test system-info ui-up ui-down ui-status

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

## restore database from backup (usage: make restore BACKUP_FILE=path/to/backup.dump)
restore:
	@$(SCRIPTS)/restore-db.sh $(BACKUP_FILE)

## create new SPEC (usage: make spec-new ID=013 NAME="memory-substrate-v2")
spec-new:
	@$(SCRIPTS)/spec-new.sh $(ID) $(NAME)

## test SPEC implementation (usage: make spec-test ID=013)
spec-test:
	@$(SCRIPTS)/spec-test.sh $(ID)

## detect system capabilities and provide recommendations
system-info:
	@$(SCRIPTS)/system-detect.sh

## UI management targets
ui-up:
	@$(SCRIPTS)/nv-ui-start.sh

ui-down:
	@$(SCRIPTS)/nv-ui-stop.sh

ui-status:
	@$(SCRIPTS)/nv-ui-status.sh
