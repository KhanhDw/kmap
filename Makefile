SHELL := /bin/bash

.PHONY: up down logs migrate test lint e2e seed-admin

up:
	docker compose up -d db
	docker compose build api
	docker compose run --rm api alembic upgrade head
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose build api
	docker compose run --rm api alembic upgrade head

test:
	docker compose exec -T api python -m pytest -q

lint:
	docker compose exec -T api python -m ruff check app tests alembic \
		/scripts/report_osm.py /scripts/make_extract_polygon.py
	docker compose build web

e2e:
	cd e2e && npm install --no-fund --no-audit
	npx playwright install --with-deps chromium || true
	npx playwright test --reporter=line

seed-admin:
	@echo "M0: không seed admin; bước seed sẽ ở M4."
