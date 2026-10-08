.PHONY: setup up down test

setup:
	./scripts/setup.sh

up:
	docker compose up --build

down:
	docker compose down

test:
	cd apps/api && .venv/bin/python -m pytest
	cd apps/web && npm test -- --run
