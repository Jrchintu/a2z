.PHONY: help install install-dev test lint format check render download clean

# Default target
help:
	@echo "A2Z DSA Sheet - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run test suite"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make format       Format code (ruff)"
	@echo "  make check        Run all checks (lint + test)"
	@echo ""
	@echo "Content:"
	@echo "  make download     Download articles from API"
	@echo "  make render       Render JSON articles to HTML"
	@echo "  make clean        Remove generated files"
	@echo ""

# Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Development
test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

check: lint test

# Content management
download:
	python -m src.download_json

render:
	python -m src.render_article

render-fast:
	python -m src.render_article --skip-localize

# Cleanup
clean:
	rm -rf public/articles/*.html
	rm -rf public/articles/*/*.html
	rm -rf public/articles/.asset_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
