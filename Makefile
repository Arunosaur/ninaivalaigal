# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb skip-mem0 with-mem0 logs

## start full stack: DB → PgBouncer → Mem0 → API
stack-up:
	@$(SCRIPTS)/nv-stack-start.sh

## stop stack: API → Mem0 → PgBouncer → DB
stack-down:
	@$(SCRIPTS)/nv-stack-stop.sh

## show status of DB, PgBouncer, Mem0, API
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

## tail logs for all containers
logs:
	@echo "== DB logs ==";        -container logs -f nv-db & \
	 echo "== PgBouncer logs =="; -container logs -f nv-pgbouncer & \
	 echo "== Mem0 logs ==";      -container logs -f nv-mem0 & \
	 echo "== API logs ==";       -container logs -f nv-api & wait
