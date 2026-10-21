SHELL := /bin/bash

.PHONY: up down logs migrate test lint e2e seed-admin

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec api alembic upgrade head

test:
	cd backend && python -m pytest -q

lint:
	cd backend && python -m ruff check app tests
	cd frontend && npm run build

e2e:
	cd e2e && npm install --no-fund --no-audit
	npx playwright install --with-deps chromium || true
	npx playwright test --reporter=line

seed-admin:
	@echo "M0: không seed admin; bước seed sẽ ở M4."
