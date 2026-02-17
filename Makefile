.PHONY: help install dev-install lint format typecheck test test-cov clean \
         db-migrate db-downgrade db-fresh docker-build docker-up docker-down \
         run-dev run-prod docs serve-docs k8s-deploy k8s-rollback

help:
	@echo "eService AI Platform - Development Commands"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install          Install production dependencies"
	@echo "  make dev-install      Install dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run code linting (ruff, pylint)"
	@echo "  make format           Format code (black)"
	@echo "  make typecheck        Type checking (mypy)"
	@echo "  make test             Run unit tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Run database migrations"
	@echo "  make db-downgrade     Rollback migrations"
	@echo "  make db-fresh         Reset and migrate fresh"
	@echo ""
	@echo "Local Development:"
	@echo "  make run-dev          Start development server"
	@echo "  make run-prod         Start production server"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start docker-compose stack"
	@echo "  make docker-down      Stop docker-compose stack"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy       Deploy to Kubernetes"
	@echo "  make k8s-rollback     Rollback Kubernetes deployment"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Generate documentation"
	@echo "  make serve-docs       Serve documentation locally"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean build artifacts"

# Setup & Dependencies
install:
	pip install --upgrade pip
	pip install -e .

dev-install:
	pip install --upgrade pip
	pip install -e ".[dev]"

# Code Quality
lint:
	ruff check src tests
	pylint src tests --disable=all --enable=E,F

format:
	black src tests
	ruff check src tests --fix

typecheck:
	mypy src

test:
	pytest -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Database
db-migrate:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-fresh:
	alembic revision --autogenerate -m "auto migration"
	alembic upgrade head

# Local Development
run-dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker
docker-build:
	docker build -f docker/Dockerfile -t eservice-platform:latest .
	docker build -f docker/Dockerfile.dev -t eservice-platform:dev .

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f api

docker-clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f

# Kubernetes
k8s-deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl rollout status deployment/eservice-api -n eservice

k8s-rollback:
	kubectl rollout undo deployment/eservice-api -n eservice
	kubectl rollout status deployment/eservice-api -n eservice

k8s-logs:
	kubectl logs -f -l app=eservice-api -n eservice

k8s-describe:
	kubectl describe pods -n eservice

# Documentation
docs:
	mkdocs build

serve-docs:
	mkdocs serve --dev-addr 0.0.0.0:8080

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf build dist *.egg-info
