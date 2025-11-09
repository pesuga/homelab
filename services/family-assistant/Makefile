# Makefile for Family Assistant - Comprehensive Test Framework

.PHONY: help install install-dev test test-unit test-integration test-e2e test-all test-cov test-watch lint format type-check security clean docker-test docker-build ci

# Default target
help:
	@echo "Family Assistant - Test Framework"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development and test dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test         - Run all tests (unit + integration)"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e     - Run end-to-end tests only"
	@echo "  test-all     - Run complete test suite (including e2e)"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  test-watch   - Run tests in watch mode"
	@echo ""
	@echo "Quality Checks:"
	@echo "  lint         - Run code linting (ruff)"
	@echo "  format       - Format code (black + isort)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  security     - Run security checks (bandit)"
	@echo ""
	@echo "Development:"
	@echo "  clean        - Clean up temporary files and artifacts"
	@echo "  docker-test  - Run tests in Docker environment"
	@echo "  docker-build - Build Docker image for testing"
	@echo "  ci           - Run complete CI pipeline"
	@echo ""
	@echo "Test Execution:"
	@echo "  test-fast    - Run fast tests only (no e2e, no external)"
	@echo "  test-slow    - Run slow tests only (marked with @slow)"
	@echo "  test-family   - Run family-specific tests only"
	@echo "  test-multimodal - Run multimodal tests only"
	@echo "  test-telegram - Run Telegram integration tests only"

# Python and pip commands
PYTHON := python3
PIP := pip3

# Directories
SRC_DIR := .
TEST_DIR := tests
REPORTS_DIR := reports
COVERAGE_DIR := $(REPORTS_DIR)/coverage
PYTEST_DIR := $(REPORTS_DIR)/pytest

# Installation
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt
	pre-commit install

# Testing
test:
	$(PYTHON) -m pytest $(TEST_DIR)/unit $(TEST_DIR)/integration -v

test-unit:
	$(PYTHON) -m pytest $(TEST_DIR)/unit -v -m "not slow"

test-integration:
	$(PYTHON) -m pytest $(TEST_DIR)/integration -v

test-e2e:
	$(PYTHON) -m pytest $(TEST_DIR)/e2e -v

test-all:
	$(PYTHON) -m pytest $(TEST_DIR) -v

test-cov:
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing --cov-report=xml

test-watch:
	$(PYTHON) -m pytest $(TEST_DIR) -f

# Specific test categories
test-fast:
	$(PYTHON) -m pytest $(TEST_DIR) -m "not slow and not external" -v

test-slow:
	$(PYTHON) -m pytest $(TEST_DIR) -m "slow" -v

test-family:
	$(PYTHON) -m pytest $(TEST_DIR) -m "family" -v

test-multimodal:
	$(PYTHON) -m pytest $(TEST_DIR) -m "multimodal" -v

test-telegram:
	$(PYTHON) -m pytest $(TEST_DIR) -m "telegram" -v

# Quality checks
lint:
	ruff check $(SRC_DIR) $(TEST_DIR)
	ruff format --check $(SRC_DIR) $(TEST_DIR)

format:
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)
	ruff format $(SRC_DIR) $(TEST_DIR)

type-check:
	mypy $(SRC_DIR)

security:
	bandit -r $(SRC_DIR)
	safety check

# Comprehensive quality check
check-all: lint type-check security test-fast

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(REPORTS_DIR)
	rm -rf .tox
	rm -rf htmlcov

# Docker testing
docker-build:
	docker build -t family-assistant-test -f Dockerfile.test .

docker-test: docker-build
	docker run --rm \
		-v $(PWD)/$(TEST_DIR):/app/$(TEST_DIR) \
		-v $(PWD)/$(SRC_DIR):/app/$(SRC_DIR) \
		family-assistant-test make test-all

# CI pipeline
ci: install-dev check-all test-all

# Development helpers
dev-setup: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

pre-commit: format lint test-fast

# Performance testing
test-performance:
	$(PYTHON) -m pytest $(TEST_DIR) -m "performance" -v --benchmark-only

# Parallel testing
test-parallel:
	$(PYTHON) -m pytest $(TEST_DIR) -n auto -v

# External service tests (requires services to be running)
test-external:
	@echo "Running external service tests (requires services to be running)..."
	$(PYTHON) -m pytest $(TEST_DIR) -m "external" -v

# Generate test reports
reports: test-cov
	@echo "Test reports generated in $(REPORTS_DIR)/"
	@echo "Coverage report: $(COVERAGE_DIR)/index.html"
	@echo "Pytest report: $(PYTEST_DIR)/report.html"

# Create directories for reports
setup-dirs:
	mkdir -p $(COVERAGE_DIR)
	mkdir -p $(PYTEST_DIR)

# Test matrix for different Python versions
test-matrix:
	@echo "Testing against Python 3.9, 3.10, 3.11, 3.12"
	for version in 3.9 3.10 3.11 3.12; do \
		if command -v python$$version >/dev/null 2>&1; then \
			echo "Testing with Python $$version"; \
			python$$version -m pytest $(TEST_DIR)/unit -v; \
		else \
			echo "Python $$version not found, skipping"; \
		fi \
	done

# Mutation testing (requires mutmut)
test-mutation:
	mutmut run --paths-to-mutate $(SRC_DIR)

# Test documentation
doctest:
	$(PYTHON) -m pytest --doctest-glob='*.md' --doctest-glob='*.rst' $(SRC_DIR)

# Profiling tests
test-profile:
	$(PYTHON) -m pytest $(TEST_DIR) --profile --profile-svg

# Stress testing
test-stress:
	$(PYTHON) -m pytest $(TEST_DIR) -m "slow" -v --dist=loadfile --numprocesses=auto

# Coverage with threshold enforcement
test-cov-strict:
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-fail-under=85 --cov-report=term-missing

# Integration with external services (requires docker-compose)
test-services:
	docker-compose -f docker-compose.test.yml up -d
	sleep 10  # Wait for services to be ready
	$(PYTHON) -m pytest $(TEST_DIR) -m "external" -v
	docker-compose -f docker-compose.test.yml down

# Memory leak detection
test-memory:
	$(PYTHON) -m pytest $(TEST_DIR) --memprof

# Race condition detection
test-race:
	$(PYTHON) -m pytest $(TEST_DIR) --race

# Fuzzing tests (requires pythonfuzz)
test-fuzz:
	$(PYTHON) -m pytest $(TEST_DIR) --fuzz