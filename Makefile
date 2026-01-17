build:
	docker compose build

start:
	docker compose up

db_migrate:
	docker compose exec api uv run alembic revision --autogenerate -m $(message)

db_upgrade:
	docker compose exec api uv run alembic upgrade head

db_downgrade:
	docker compose exec api uv run alembic downgrade -1

db_empty_revision:
	docker compose exec api uv run alembic revision -m $(message)

test:
	PYTHONPATH=${PYTHONPATH}:`pwd` uv run pytest src/tests -vv

pre_commit:
	PYTHONPATH=${PYTHONPATH}:`pwd` uv run pre-commit run --all-files --verbose
