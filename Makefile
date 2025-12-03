build:
	docker compose build

start:
	docker compose up

db_migrate:
	docker compose exec api poetry run alembic revision --autogenerate -m $(message)

db_upgrade:
	docker compose exec api poetry run alembic upgrade head

db_downgrade:
	docker compose exec api poetry run alembic downgrade -1

db_empty_revision:
	docker compose exec api poetry run alembic revision -m $(message)

test:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run pytest src/tests -vv

pre_commit:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run pre-commit run --all-files --verbose
