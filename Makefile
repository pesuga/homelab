# Family AI Platform Makefile
.PHONY: help install dev test clean build deploy stop logs health

# Default target
help: ## Show this help message
	@echo "Family AI Platform - Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install and start all services
	@echo "🚀 Installing Family AI Platform..."
	docker-compose up -d
	@echo "✅ Installation complete! Access at http://localhost:3000"

dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	docker-compose up --build

build: ## Build all Docker images
	@echo "🏗️ Building Docker images..."
	docker-compose build

# Service management
start: ## Start all services
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API service logs
	docker-compose logs -f family-ai-api

logs-voice: ## Show voice service logs
	docker-compose logs -f voice-service

# Database management
db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	docker-compose exec postgres psql -U family_ai -d family_ai -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@echo "✅ Database reset complete"

db-migrate: ## Run database migrations
	docker-compose exec family-ai-api alembic upgrade head

# Testing
test: ## Run all tests
	docker-compose exec family-ai-api pytest

test-unit: ## Run unit tests
	docker-compose exec family-ai-api pytest tests/unit/

test-integration: ## Run integration tests
	docker-compose exec family-ai-api pytest tests/integration/

# Development tools
shell-api: ## Open shell in API container
	docker-compose exec family-ai-api /bin/bash

shell-db: ## Open database shell
	docker-compose exec postgres psql -U family_ai -d family_ai

# Health and monitoring
health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/api/v1/health | python3 -m json.tool || echo "API: Unhealthy"
	@docker-compose ps

status: ## Show status of all services
	docker-compose ps

# Cleanup
clean: ## Clean up Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

clean-images: ## Remove all Docker images
	docker rmi $(shell docker images -q "family-ai-*") 2>/dev/null || true
	@echo "✅ Docker images cleaned"

# Configuration
config: ## Generate environment configuration
	@echo "📝 Generating configuration..."
	cp .env.example .env
	@echo "✅ Configuration created at .env"
	@echo "   Please edit .env with your settings"

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	# Add staging deployment logic here
	@echo "✅ Staging deployment complete"

deploy-production: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	# Add production deployment logic here
	@echo "✅ Production deployment complete"

# Backup and restore
backup: ## Backup all data
	@echo "💾 Creating backup..."
	mkdir -p backups
	docker-compose exec postgres pg_dump -U family_ai family_ai > backups/db-backup-$(shell date +%Y%m%d).sql
	@echo "✅ Backup complete: backups/db-backup-$(shell date +%Y%m%d).sql"

restore: ## Restore from backup (usage: make restore BACKUP_FILE=filename)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Usage: make restore BACKUP_FILE=filename"; exit 1; fi
	@echo "🔄 Restoring from backup: $(BACKUP_FILE)"
	docker-compose exec -T postgres psql -U family_ai -d family_ai < $(BACKUP_FILE)
	@echo "✅ Restore complete"

# Development utilities
install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r core/requirements-dev.txt
	npm install --prefix integrations/mobile
	@echo "✅ Development dependencies installed"

format: ## Format code
	@echo "🎨 Formatting code..."
	docker-compose exec family-ai-api black .
	docker-compose exec family-ai-api isort .
	@echo "✅ Code formatted"

lint: ## Run linting
	@echo "🔍 Running linting..."
	docker-compose exec family-ai-api flake8 .
	docker-compose exec family-ai-api mypy .
	@echo "✅ Linting complete"

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	docker-compose exec family-ai-api bandit -r .
	docker-compose exec family-ai-api safety check
	@echo "✅ Security checks complete"