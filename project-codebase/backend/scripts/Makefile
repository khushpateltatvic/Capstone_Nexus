# 🐳 Project Nexus Backend - Docker Commands

.PHONY: help build up down logs clean dev prod test health

# Default target
help: ## Show this help message
	@echo "🐳 Project Nexus Backend - Docker Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment with hot reload
	docker compose -f docker-compose.dev.yml up --build

dev-bg: ## Start development environment in background
	docker compose -f docker-compose.dev.yml up -d --build

# Production commands
prod: ## Start production environment
	docker compose up --build -d

build: ## Build the Docker image
	docker compose build

build-no-cache: ## Build without cache
	docker compose build --no-cache

# Control commands
up: ## Start services
	docker compose up -d

down: ## Stop and remove services
	docker compose down

restart: ## Restart services
	docker compose restart

# Monitoring commands
logs: ## Show logs
	docker compose logs -f

logs-backend: ## Show backend logs only
	docker compose logs -f backend

health: ## Check container health
	docker compose ps

status: ## Detailed status
	@echo "📊 Container Status:"
	@docker compose ps
	@echo ""
	@echo "🏥 Health Check:"
	@docker inspect project_nexus_backend | grep Health -A 5 || echo "Health check not available"

# Utility commands
shell: ## Enter container shell
	docker compose exec backend bash

clean: ## Clean up Docker resources
	docker compose down -v
	docker system prune -f

clean-all: ## Clean up everything including images
	docker compose down -v --rmi all
	docker system prune -af

# Testing commands
test: ## Run tests in container
	docker compose exec backend python -m pytest

test-health: ## Test health endpoint
	curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Production deployment
deploy-staging: ## Deploy to staging
	@echo "🚀 Deploying to staging..."
	docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

deploy-production: ## Deploy to production
	@echo "🚀 Deploying to production..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Backup and restore
backup: ## Backup volumes
	@echo "💾 Creating backup..."
	docker run --rm -v logs_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/logs-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .

restore: ## Restore from backup (usage: make restore BACKUP=logs-20240203-143000.tar.gz)
	@if [ -z "$(BACKUP)" ]; then echo "❌ Please specify BACKUP=filename.tar.gz"; exit 1; fi
	docker run --rm -v logs_data:/data -v $(PWD)/backups:/backup alpine tar xzf /backup/$(BACKUP) -C /data

# Quick start
quick-start: ## Quick development setup
	@echo "🚀 Quick starting Project Nexus Backend..."
	make build
	make dev-bg
	make health
	@echo "✅ Backend is starting at http://localhost:8000"
	@echo "📊 Check status with: make health"
	@echo "📋 View logs with: make logs"

# Full reset
reset: ## Full reset - stop, clean, rebuild, start
	@echo "🔄 Full reset in progress..."
	make down
	make clean
	make build
	make up
	@echo "✅ Reset complete!"
