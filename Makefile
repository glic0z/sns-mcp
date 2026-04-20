.PHONY: install test lint run run-http docker-up docker-logs clean

# ─── Install & Setup ────────────────────────────────────
install:
	@echo "=== stormshield-mcp: Install & Setup ==="
	python -m pip install -e ".[dev]"

# ─── Testing ────────────────────────────────────────────
test:
	@echo "=== Running tests with coverage ==="
	python -m pytest tests/unit/ \
		--cov=src/stormshield_mcp \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-fail-under=45 \
		-v

# ─── Linting ────────────────────────────────────────────
lint:
	@echo "=== Ruff check ==="
	python -m ruff check src/ tests/
	@echo "=== Ruff format check ==="
	python -m ruff format --check src/ tests/
	@echo "=== Mypy ==="
	python -m mypy src/

# ─── Run Servers ────────────────────────────────────────
run:
	stormshield-mcp --config config/config.yaml

run-http:
	stormshield-mcp --config config/config.yaml --transport http

# ─── Docker ─────────────────────────────────────────────
docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f

# ─── Clean ──────────────────────────────────────────────
clean:
	@echo "=== Cleaning ==="
	rm -rf venv .venv __pycache__ .coverage htmlcov .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done."
