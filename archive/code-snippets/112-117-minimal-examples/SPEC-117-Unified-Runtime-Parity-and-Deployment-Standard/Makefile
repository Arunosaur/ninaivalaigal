RUNTIME ?= docker

.PHONY: up down build logs

build:
	$(RUNTIME) compose build

up:
	$(RUNTIME) compose up -d

down:
	$(RUNTIME) compose down

logs:
	$(RUNTIME) compose logs -f
