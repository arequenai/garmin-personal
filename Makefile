.PHONY: dev-db dev-api dev-web migrate sync lint format test

# Start PostgreSQL in Docker
dev-db:
	docker compose up -d

# Start FastAPI backend
dev-api:
	cd apps/sync && uv run uvicorn app.main:app --reload --port 8000

# Start Next.js frontend
dev-web:
	cd apps/web && pnpm dev

# Run database migrations
migrate:
	cd apps/sync && uv run alembic upgrade head

# Trigger a manual sync (yesterday's data)
sync:
	curl -X POST http://localhost:8000/api/sync/trigger

# Sync with custom days back
sync-days:
	@read -p "Days back: " days; \
	curl -X POST "http://localhost:8000/api/sync/trigger?days_back=$$days"

# Lint all code
lint:
	cd apps/sync && uv run ruff check .
	cd apps/web && pnpm lint

# Format all code
format:
	cd apps/sync && uv run ruff format .
	cd apps/web && npx prettier --write "src/**/*.{ts,tsx}"

# Run Python tests
test:
	cd apps/sync && uv run pytest tests/ -v

# Full check before commit
check: lint test
	cd apps/web && pnpm build

# Initial setup
setup: dev-db
	cd apps/sync && uv sync
	cd apps/web && pnpm install
	$(MAKE) migrate
	@echo ""
	@echo "Setup complete! Copy .env.example to .env and fill in your credentials."
	@echo "Then run: make dev-db && make dev-api (terminal 1) && make dev-web (terminal 2)"
