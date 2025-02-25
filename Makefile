# Makefile
SERVICE_NAME := openai-in-a-box
DOCKER_COMPOSE := docker compose
DOCKER_BUILD := docker build --no-cache
PORT := 8080
HOST := 0.0.0.0
VENV := .venv
PYTHON := $(VENV)/bin/python

export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

.DEFAULT_GOAL := help

# Help Function
.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker targets
.PHONY: docker-build
docker-build: ## Build Docker image
	$(DOCKER_BUILD) -t $(SERVICE_NAME) .

.PHONY: docker-up
docker-up: ## Start Docker containers
	$(DOCKER_COMPOSE) up -d --remove-onsha

.PHONY: docker-down
docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) down

.PHONY: docker-logs
docker-logs: ## Show Docker container logs
	$(DOCKER_COMPOSE) logs -f --tail=100

.PHONY: deploy
deploy: ## Show deploy
	DOCKER_BUILDKIT=1 $(DOCKER_COMPOSE) up -d --build --remove-orphans --force-recreate


# Local development targets
.PHONY: venv
venv: ## Create Python virtual environment
	python -m virtualenv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: dev
dev: ## Start local development server
	@echo "Starting development server..."
	uvicorn main:app --reload --port $(PORT) --host $(HOST) --reload-dir server

.PHONY: prod
prod: ## Start production server
	@echo "Starting production server..."
	@nohup uvicorn main:app --port $(PORT) --host $(HOST) > app.log 2>&1 &

# Utility targets
.PHONY: clean
clean: ## Clean project
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -exec rm -f {} +
	python -c "import torch; torch.cuda.empty_cache()"

.PHONY: stop
stop: ## Stop production server
	@echo "Stopping production server..."
	@kill -9 $$(lsof -t -i:$(PORT)) 2>/dev/null || true

.PHONY: openapi
openapi:
	curl -X GET "http://$(HOST):$(PORT)/openapi.json" -H "accept: application/json" > openapi.json

.PHONY: lint
lint: venv ## Run code linter
	@$(VENV)/bin/flake8 .

.PHONY: test
test: venv ## Run tests
	@$(VENV)/bin/pytest -v tests/

.PHONY: deps
deps: ## Update dependencies
	@$(VENV)/bin/pip freeze > requirements.txt

.PHONY: count
count:
	python ./scripts/count_codelines.py

.PHONY: install
install: venv
	@$(VENV)/bin/pip install --upgrade pip
	@$(VENV)/bin/pip install --no-cache-dir --no-deps -r requirements.txt