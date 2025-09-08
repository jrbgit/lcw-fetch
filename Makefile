# Makefile for LCW API Fetcher
# Provides common development and testing tasks

.PHONY: help install install-dev test test-unit test-integration test-coverage test-fast lint format type-check security clean build docker docs

# Default target
help:
	@echo "Available targets:"
	@echo "  help              Show this help message"
	@echo "  install           Install production dependencies"
	@echo "  install-dev       Install development and test dependencies"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run only unit tests"
	@echo "  test-integration  Run only integration tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-fast         Run tests excluding slow ones"
	@echo "  lint              Run linting (flake8)"
	@echo "  format            Format code (black + isort)"
	@echo "  format-check      Check code formatting"
	@echo "  type-check        Run type checking (mypy)"
	@echo "  security          Run security checks (bandit + safety)"
	@echo "  clean             Clean build artifacts and cache"
	@echo "  build             Build Python package"
	@echo "  docker            Build Docker image"
	@echo "  docker-test       Run tests in Docker container"
	@echo "  docs              Generate documentation"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install -e .

# Testing targets
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

test-fast:
	pytest -m "not slow" --tb=short

test-parallel:
	pytest -n auto

test-watch:
	ptw --runner "pytest --tb=short"

# Code quality targets
lint:
	flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black src tests
	isort src tests

format-check:
	black --check --diff src tests
	isort --check-only --diff src tests

type-check:
	mypy src --ignore-missing-imports

# Security targets
security:
	bandit -r src/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "Security reports generated: bandit-report.json, safety-report.json"

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

build: clean
	python -m build
	twine check dist/*

# Docker targets
docker:
	docker build -t lcw-api-fetcher .

docker-test:
	docker build -t lcw-api-fetcher-test -f Dockerfile.test .
	docker run --rm lcw-api-fetcher-test

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Documentation targets
docs:
	@echo "Documentation generation would go here"
	@echo "Consider using Sphinx or mkdocs"

# Development environment setup
setup-dev: install-dev
	pre-commit install || echo "pre-commit not available"
	@echo "Development environment set up successfully"

# CI simulation
ci-local: format-check lint type-check security test-coverage
	@echo "Local CI checks completed"

# Database management (for development)
db-up:
	docker run -d --name influxdb-dev \
		-p 8086:8086 \
		-e DOCKER_INFLUXDB_INIT_MODE=setup \
		-e DOCKER_INFLUXDB_INIT_USERNAME=admin \
		-e DOCKER_INFLUXDB_INIT_PASSWORD=admin123 \
		-e DOCKER_INFLUXDB_INIT_ORG=dev_org \
		-e DOCKER_INFLUXDB_INIT_BUCKET=dev_bucket \
		-e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=dev_token_123 \
		influxdb:2.7

db-down:
	docker stop influxdb-dev || true
	docker rm influxdb-dev || true

# Utility targets
check-env:
	@echo "Checking environment variables..."
	@python -c "import os; print('LCW_API_KEY:', 'SET' if os.getenv('LCW_API_KEY') else 'NOT SET')"
	@python -c "import os; print('INFLUX_URL:', os.getenv('INFLUX_URL', 'NOT SET'))"
	@python -c "import os; print('INFLUX_TOKEN:', 'SET' if os.getenv('INFLUX_TOKEN') else 'NOT SET')"
	@python -c "import os; print('INFLUX_ORG:', os.getenv('INFLUX_ORG', 'NOT SET'))"
	@python -c "import os; print('INFLUX_BUCKET:', os.getenv('INFLUX_BUCKET', 'NOT SET'))"

version:
	@python -c "import src.lcw_fetcher; print(src.lcw_fetcher.__version__)" 2>/dev/null || echo "Version not found"

requirements-update:
	pip-compile requirements.in
	pip-compile requirements-test.in

# Release targets
tag-version:
	@echo "Current version: $$(python setup.py --version)"
	@read -p "Enter new version: " version && \
	git tag -a "v$$version" -m "Release version $$version" && \
	git push origin "v$$version"
