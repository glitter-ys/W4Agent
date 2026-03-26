.PHONY: help install dev build up down logs migrate test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Development ===

install: ## Install all dependencies
	cd backend && pip install -e ".[dev]"
	cd backend && playwright install chromium
	cd frontend && npm install

dev-backend: ## Start backend dev server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

dev: ## Start both backend and frontend (requires tmux)
	@echo "Starting backend..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	@cd frontend && npm run dev

# === Docker ===

up: ## Start all services with Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build Docker images
	docker compose build

logs: ## View logs
	docker compose logs -f

# === Database ===

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

# === Testing ===

test: ## Run backend tests
	cd backend && pytest -v

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov=agent --cov=crawler --cov=detector -v

# === Utility ===

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache
	rm -rf frontend/dist frontend/node_modules/.vite

lint: ## Run linters
	cd backend && ruff check .
	cd frontend && npm run lint

format: ## Format code
	cd backend && ruff format .
