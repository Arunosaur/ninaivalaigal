# Next.js Frontend Development Makefile
# SPEC-103: Next.js 15 Bootstrap

.PHONY: help install dev build start lint lint-fix type-check format format-check clean test

help: ## Show this help message
	@echo "Next.js Frontend Development Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (npm ci for reproducible builds)
	npm ci

dev: install ## Install deps and start dev server (one-command startup)
	@echo "🚀 Starting Next.js development server..."
	npm run dev

build: ## Build production bundle
	npm run build

start: ## Start production server (requires build first)
	npm run start

lint: ## Run ESLint
	npm run lint

lint-fix: ## Run ESLint with auto-fix
	npm run lint:fix

type-check: ## Run TypeScript type checking
	npm run type-check

format: ## Format code with Prettier
	npm run format

format-check: ## Check code formatting
	npm run format:check

clean: ## Clean build artifacts and node_modules
	rm -rf .next out node_modules .turbo

test: lint type-check ## Run all checks (lint + type-check)
	@echo "✅ All checks passed!"

ci: install test build ## Full CI pipeline (install, test, build)
	@echo "✅ CI pipeline complete!"
