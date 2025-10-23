# Weekly Report Pipeline Makefile

.PHONY: install run test clean help

# Default week
WEEK ?= 2025-42

# Python executable
PYTHON := python

help: ## Show this help message
	@echo "Weekly Report Pipeline"
	@echo "====================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e .

run: ## Generate reports for specified week (use WEEK=2025-42)
	$(PYTHON) -m weekly_report.src.cli generate --week $(WEEK)

test: ## Run tests
	pytest tests/ -v

clean: ## Clean generated files
	rm -rf data/curated/
	rm -rf charts/
	rm -rf reports/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev-install: ## Install with dev dependencies
	pip install -e ".[dev]"

lint: ## Run linting
	black src/ tests/
	isort src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

