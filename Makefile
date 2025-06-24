# Makefile for Shipra Backend

.PHONY: help build run stop clean logs shell test lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  build        - Build Docker images"
	@echo "  run          - Start all services"
	@echo "  run-dev      - Start development environment"
	@echo "  stop         - Stop all services"
	@echo "  clean        - Remove containers and volumes"
	@echo "  logs         - Show application logs"
	@echo "  shell        - Open shell in running container"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  health       - Check service health"
	@echo "  monitor      - Start monitoring stack"

# Build Docker images
build:
	docker-compose build

# Start production environment
run:
	docker-compose up -d

# Start development environment
run-dev:
	docker-compose --profile dev up -d

# Start monitoring stack
monitor:
	docker-compose --profile monitoring up -d

# Start production stack with nginx
run-prod:
	docker-compose --profile production up -d

# Stop all services
stop:
	docker-compose down

# Remove containers and volumes
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Show application logs
logs:
	docker-compose logs -f shipra-backend

# Show all logs
logs-all:
	docker-compose logs -f

# Open shell in running container
shell:
	docker-compose exec shipra-backend /bin/bash

# Run tests
test:
	docker-compose exec shipra-backend pytest

# Run linting
lint:
	docker-compose exec shipra-backend flake8 src/
	docker-compose exec shipra-backend mypy src/

# Format code
format:
	docker-compose exec shipra-backend black src/
	docker-compose exec shipra-backend isort src/

# Check service health
health:
	curl -f http://localhost:8000/health || echo "Service is not healthy"

# Check readiness
ready:
	curl -f http://localhost:8000/ready || echo "Service is not ready"

# Database operations
db-shell:
	docker-compose exec postgres psql -U shipra -d shipra_db

db-backup:
	docker-compose exec postgres pg_dump -U shipra shipra_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	docker-compose exec -T postgres psql -U shipra -d shipra_db < $(file)

# Redis operations
redis-shell:
	docker-compose exec redis redis-cli

# Development helpers
install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit

setup-pre-commit:
	pre-commit install

# Production helpers
deploy:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

rollback:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitoring
grafana:
	@echo "Grafana available at: http://localhost:3000 (admin/admin)"
	@echo "Prometheus available at: http://localhost:9090"

# Quick start for development
dev: build run-dev
	@echo "Development environment started!"
	@echo "Application: http://localhost:8001"
	@echo "Database: localhost:5432"
	@echo "Redis: localhost:6379"

# Quick start for production
prod: build run-prod
	@echo "Production environment started!"
	@echo "Application: http://localhost:8000"
	@echo "Nginx: http://localhost:80"

# Show service status
status:
	docker-compose ps 