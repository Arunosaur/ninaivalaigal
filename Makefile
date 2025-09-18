# Makefile for ninaivalaigal stack (Apple container)

SCRIPTS := scripts

.PHONY: stack-up stack-down stack-status db-only skip-api skip-pgb logs

## start full stack: DB → PgBouncer → API
stack-up:
	@$(SCRIPTS)/nv-stack-start.sh

## stop stack: API → PgBouncer → DB
stack-down:
	@$(SCRIPTS)/nv-stack-stop.sh

## show status of DB, PgBouncer, API
stack-status:
	@$(SCRIPTS)/nv-stack-status.sh

## bring up only the database
db-only:
	@$(SCRIPTS)/nv-stack-start.sh --db-only

## bring up DB + PgBouncer but skip API
skip-api:
	@$(SCRIPTS)/nv-stack-start.sh --skip-api

## bring up DB + API but skip PgBouncer
skip-pgb:
	@$(SCRIPTS)/nv-stack-start.sh --skip-pgb

## tail logs for all containers
logs:
	@echo "== DB logs ==";        -container logs -f nv-db & \
	 echo "== PgBouncer logs =="; -container logs -f nv-pgbouncer & \
	 echo "== API logs ==";       -container logs -f nv-api & wait
