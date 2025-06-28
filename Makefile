.PHONY: help install install-dev test test-verbose test-unit test-integration test-slow test-coverage
.PHONY: lint format clean build run run-dev run-chainlit run-backend run-docker
.PHONY: docker-build docker-up docker-down docker-logs
.PHONY: build-vector-store start-services stop-services health-check
.PHONY: freeze requirements docs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION := 3.13
PROJECT_NAME := lets-talk
BACKEND_DIR := backend
TESTS_DIR := tests
DOCKER_COMPOSE_FILE := docker-compose.yml

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(BLUE)$(PROJECT_NAME) Development Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Installation targets
install: ## Install production dependencies using uv
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	uv sync --no-dev

install-dev: ## Install all dependencies including dev dependencies using uv
	@echo "$(GREEN)Installing all dependencies (including dev)...$(NC)"
	uv sync

install-force: ## Force reinstall all dependencies
	@echo "$(GREEN)Force reinstalling all dependencies...$(NC)"
	uv sync --reinstall

# Testing targets
test: ## Run all tests using pytest
	@echo "$(GREEN)Running all tests...$(NC)"
	uv run pytest

test-verbose: ## Run tests with verbose output
	@echo "$(GREEN)Running tests with verbose output...$(NC)"
	uv run pytest -v

test-unit: ## Run only unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"
	uv run pytest -m "unit" -v

test-integration: ## Run only integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	uv run pytest -m "integration" -v

test-slow: ## Run all tests including slow ones
	@echo "$(GREEN)Running all tests (including slow)...$(NC)"
	uv run pytest -v

test-fast: ## Run tests excluding slow ones
	@echo "$(GREEN)Running fast tests only...$(NC)"
	uv run pytest -m "not slow" -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	uv run pytest --cov=lets_talk --cov-report=html --cov-report=term

test-file: ## Run specific test file (usage: make test-file FILE=test_filename.py)
	@echo "$(GREEN)Running test file: $(FILE)$(NC)"
	uv run pytest $(TESTS_DIR)/$(FILE) -v

test-function: ## Run specific test function (usage: make test-function FILE=test_file.py FUNC=test_function_name)
	@echo "$(GREEN)Running test function: $(FUNC) in $(FILE)$(NC)"
	uv run pytest $(TESTS_DIR)/$(FILE)::$(FUNC) -v

# Code quality targets
lint: ## Run linting checks
	@echo "$(GREEN)Running lint checks...$(NC)"
	uv run ruff check .
	uv run mypy backend/lets_talk

format: ## Format code using ruff
	@echo "$(GREEN)Formatting code...$(NC)"
	uv run ruff format .
	uv run ruff check --fix .

check: ## Run all code quality checks
	@echo "$(GREEN)Running all code quality checks...$(NC)"
	$(MAKE) lint
	$(MAKE) format

# Application targets
run: ## Run the main application
	@echo "$(GREEN)Running main application...$(NC)"
	uv run python main.py

run-dev: ## Run the application in development mode
	@echo "$(GREEN)Running application in development mode...$(NC)"
	uv run python -m backend.app

run-chainlit: ## Run the Chainlit interface
	@echo "$(GREEN)Starting Chainlit interface...$(NC)"
	uv run chainlit run backend/app.py -w

run-backend: ## Run the FastAPI backend
	@echo "$(GREEN)Starting FastAPI backend...$(NC)"
	cd $(BACKEND_DIR) && uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000

run-demo: ## Run the demo pipeline
	@echo "$(GREEN)Running demo pipeline...$(NC)"
	uv run python demo_pipeline.py

# Docker targets
docker-build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

docker-up: ## Start Docker services
	@echo "$(GREEN)Starting Docker services...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

docker-down: ## Stop Docker services
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

docker-logs: ## Show Docker logs
	@echo "$(GREEN)Showing Docker logs...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

docker-restart: ## Restart Docker services
	@echo "$(GREEN)Restarting Docker services...$(NC)"
	$(MAKE) docker-down
	$(MAKE) docker-up

docker-clean: ## Clean Docker resources
	@echo "$(GREEN)Cleaning Docker resources...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

# Build and setup targets
build: ## Build the project
	@echo "$(GREEN)Building project...$(NC)"
	uv build

build-vector-store: ## Build vector store using script
	@echo "$(GREEN)Building vector store...$(NC)"
	./scripts/build-vector-store.sh

# Service management
start-services: ## Start all required services
	@echo "$(GREEN)Starting all services...$(NC)"
	$(MAKE) docker-up
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	sleep 10

stop-services: ## Stop all services
	@echo "$(GREEN)Stopping all services...$(NC)"
	$(MAKE) docker-down

restart-services: ## Restart all services
	@echo "$(GREEN)Restarting all services...$(NC)"
	$(MAKE) stop-services
	$(MAKE) start-services

health-check: ## Check health of services
	@echo "$(GREEN)Checking service health...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps

# Utility targets
clean: ## Clean build artifacts and cache
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

clean-all: ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	$(MAKE) clean
	$(MAKE) docker-clean

freeze: ## Generate requirements.txt using uv
	@echo "$(GREEN)Generating requirements.txt...$(NC)"
	uv pip freeze > requirements.txt

requirements: ## Install dependencies from requirements.txt
	@echo "$(GREEN)Installing from requirements.txt...$(NC)"
	uv pip install -r requirements.txt

# Environment setup
setup: ## Initial project setup
	@echo "$(GREEN)Setting up project...$(NC)"
	$(MAKE) install-dev
	@echo "$(YELLOW)Project setup complete! Run 'make help' to see available commands.$(NC)"

setup-prod: ## Setup for production
	@echo "$(GREEN)Setting up for production...$(NC)"
	$(MAKE) install
	$(MAKE) build-vector-store

# Development helpers
dev: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(MAKE) start-services
	$(MAKE) run-chainlit

notebook: ## Start Jupyter notebook server
	@echo "$(GREEN)Starting Jupyter notebook server...$(NC)"
	cd $(BACKEND_DIR)/notebooks && uv run jupyter notebook

# Validation and final checks
validate: ## Run final validation script
	@echo "$(GREEN)Running final validation...$(NC)"
	./scripts/final_validation.sh

test-incremental: ## Test incremental system
	@echo "$(GREEN)Testing incremental system...$(NC)"
	./scripts/test_incremental_system.sh

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

# Quick development cycle
quick-test: ## Quick test cycle (install deps, run tests)
	@echo "$(GREEN)Running quick test cycle...$(NC)"
	$(MAKE) install-dev
	$(MAKE) test-fast

quick-check: ## Quick quality check (format, lint, test)
	@echo "$(GREEN)Running quick quality check...$(NC)"
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test-fast

# Show project status
status: ## Show project status
	@echo "$(BLUE)Project Status:$(NC)"
	@echo "$(YELLOW)Python version:$(NC) $(PYTHON_VERSION)"
	@echo "$(YELLOW)Project name:$(NC) $(PROJECT_NAME)"
	@echo "$(YELLOW)UV version:$(NC)"
	@uv --version
	@echo "$(YELLOW)Docker status:$(NC)"
	@docker --version 2>/dev/null || echo "Docker not available"
	@echo "$(YELLOW)Services status:$(NC)"
	@$(MAKE) health-check 2>/dev/null || echo "Services not running"

# Emergency stops
kill: ## Force stop all related processes
	@echo "$(RED)Force stopping all processes...$(NC)"
	pkill -f "chainlit" || true
	pkill -f "uvicorn" || true
	pkill -f "jupyter" || true
	$(MAKE) docker-down

# Show logs
logs: ## Show application logs
	@echo "$(GREEN)Showing application logs...$(NC)"
	$(MAKE) docker-logs
