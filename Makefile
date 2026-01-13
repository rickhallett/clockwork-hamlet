.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend lint lint-backend lint-frontend format format-backend test test-backend seed simulate clean clean-all sync

help:
	@echo "Clockwork Hamlet Development Commands"
	@echo ""
	@echo "  make install         Install all dependencies"
	@echo "  make sync            Sync Python dependencies with uv"
	@echo "  make dev             Run both backend and frontend"
	@echo "  make dev-backend     Run backend only"
	@echo "  make dev-frontend    Run frontend only"
	@echo "  make lint            Lint all code"
	@echo "  make lint-backend    Lint Python code"
	@echo "  make lint-frontend   Lint TypeScript code"
	@echo "  make format          Format all code"
	@echo "  make test            Run all tests"
	@echo "  make clean           Clean build artifacts"

# Installation
install: install-backend install-frontend

install-backend: sync

sync:
	cd backend && uv sync

install-frontend:
	cd frontend && bun install

# Development
dev:
	@echo "Starting backend and frontend..."
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uv run python -m hamlet.main

dev-frontend:
	cd frontend && bun run dev

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check src tests
	cd backend && uv run ruff format --check src tests

lint-frontend:
	cd frontend && bun run lint

# Format
format: format-backend

format-backend:
	cd backend && uv run ruff format src tests
	cd backend && uv run ruff check --fix src tests

# Testing
test: test-backend

test-backend:
	cd backend && uv run pytest

# Seed database
seed:
	cd backend && uv run python -m hamlet.db.seed

# Run simulation
simulate:
	cd backend && uv run python -m hamlet.simulation.engine --ticks 10

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true

# Deep clean (removes venv, requires re-sync)
clean-all: clean
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
