.PHONY: help test test-unit test-integration test-security test-validation test-e2e test-fast test-cov coverage test-html clean install lint

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt

test:  ## Run all tests
	pytest -v

test-unit:  ## Run unit tests only
	@echo "Note: Most tests don't have markers yet. Running all tests..."
	pytest -v

test-integration:  ## Run integration tests only
	@echo "Note: Running migration and postgres tests..."
	pytest tests/test_migration/ tests/test_postgres/ -v

test-security:  ## Run security tests only
	pytest tests/test_security/ -v

test-validation:  ## Run validation tests only
	pytest tests/test_validation/ -v

test-e2e:  ## Run end-to-end tests only
	pytest tests/test_workflows/ -v

test-fast:  ## Run tests excluding slow tests
	pytest -v

test-cov:  ## Run tests with coverage report
	pytest --cov=skills --cov-report=term-missing --cov-report=html -v
	@echo "\nOpening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"

coverage: test-cov  ## Alias for test-cov

test-html:  ## Run tests and open HTML coverage report
	pytest --cov=skills --cov-report=html -v
	open htmlcov/index.html || xdg-open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	pytest-watch

test-verbose:  ## Run tests with verbose output
	pytest -vv

test-failed:  ## Re-run only failed tests
	pytest --lf

lint:  ## Lint YAML files
	yamllint shared/*.yaml shared/*.yml || true

clean:  ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

coverage-badge:  ## Generate coverage badge
	@coverage report | grep TOTAL | awk '{print "Coverage: " $$4}'

ci:  ## Run CI pipeline locally
	make lint
	make test-cov

.DEFAULT_GOAL := help
