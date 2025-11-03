.PHONY: start
start:
	poetry run uvicorn src.api_server.main:app --port 5000 --reload

install:
	poetry install --no-root

db_init:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run alembic init alembic

db_migrate:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run alembic revision --autogenerate -m $(message)

db_upgrade:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run alembic upgrade head

db_downgrade:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run alembic downgrade -1

db_empty_revision:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run alembic revision -m $(message)

test:
	poetry run pytest src/tests -vv

pre_commit:
	PYTHONPATH=${PYTHONPATH}:`pwd` poetry run pre-commit run --all-files --verbose
