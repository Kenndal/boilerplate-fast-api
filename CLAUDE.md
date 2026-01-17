# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note**: This project uses **uv** for dependency management instead of Poetry.

## Development Commands

### Docker Environment (Primary Workflow)
```bash
make build          # Build Docker containers
make start          # Start all services (PostgreSQL + FastAPI on port 5000)
make test           # Run pytest test suite (runs outside Docker with PYTHONPATH set)
make pre_commit     # Run all pre-commit hooks (black, isort, flake8, mypy)
```

### Database Migrations
```bash
make db_migrate message="description"      # Auto-generate migration from entity changes
make db_empty_revision message="description"  # Create empty migration for data changes
make db_upgrade                            # Apply all pending migrations
make db_downgrade                          # Rollback one migration
```

### Running Individual Tests
```bash
PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_user_service.py -vv
PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_user_service.py::test_function_name -vv
```

## Architecture Overview

This is a **layered FastAPI application** with strict separation of concerns. Data flows unidirectionally from API → Service → Data Service → Database.

### Layer Dependencies (Top to Bottom)
1. **API Layer** (`src/api_server/`) - HTTP handling, FastAPI routers, OpenAPI docs
2. **Service Layer** (`src/services/`) - Business logic, Result pattern error handling
3. **Data Service Layer** (`src/data_services/`) - Database operations, query building
4. **Database Layer** (`src/database/`) - SQLAlchemy entities and engine setup

**Critical Rule**: Each layer only imports from layers below it. Never import from layers above.

### Key Architectural Patterns

#### Result Pattern for Error Handling
Services return `Result[T, ErrorResult]` instead of raising exceptions:
```python
Result[User, ErrorResult]  # Success = User, Failure = ErrorResult
```
- Router layer pattern matches on Result and converts to HTTP exceptions
- Service layer catches CRUD exceptions and returns ErrorResult
- Makes error cases explicit in type signatures

#### Generic CRUD System
- `Crud[Entity, CreateModel, UpdateModel]` - Generic data access for any entity
- `BaseService[Entity, Model, CreateModel, UpdateModel]` - Generic business logic
- `ModelToEntityMapper` - Protocol for transforming Pydantic models to entities
- Entities extend `BaseAuditEntity` for standardized audit fields (created_date, last_modified_date, created_by_user_id, last_modified_by_user_id, is_active)

#### Dependency Injection Pattern
All dependencies flow through `src/api_server/deps.py`:
- `get_db()` - Provides SQLAlchemy Session with automatic transaction management
- `get_*_data_service()` - Injects Session into data services
- `get_*_service()` - Injects data services into business services

Transaction management is automatic: commits on success, rollbacks on exception, session closed after request.

#### Schema-Aware Database
- All entities use configurable schema (default: `sample_schema`)
- Schema defined in `config.DATABASE_SCHEMA`
- Alembic migrations respect schema configuration

## Adding New Entities

Follow this exact sequence to maintain architectural consistency:

1. **Entity** - Create SQLAlchemy model in `src/database/entities/`, extend `Base` and `BaseAuditEntity`
2. **Pydantic Models** - Create `*Create`, `*Update`, and read model in `src/models/`
3. **Mapper** - Create `*_create_model_to_entity()` function in `src/mappers/`
4. **Data Service** - Create class extending `Crud[Entity, CreateModel, UpdateModel]` in `src/data_services/`
5. **Service** - Create class extending `BaseService[Entity, Model, CreateModel, UpdateModel]` in `src/services/`, set `model_class` attribute
6. **Router** - Create router in `src/api_server/routers/`, register in `main.py`
7. **Dependency Provider** - Add `get_*_service()` and `get_*_data_service()` in `src/api_server/deps.py`
8. **Migration** - Run `make db_migrate message="add_entity_name"` then `make db_upgrade`

## Code Quality Standards

### Type Safety (Strict mypy)
- All functions require type annotations
- Use generics (`Entity: Base`, `Model: BaseModel`) for reusable components
- Leverage Protocol-based design (see `ModelToEntityMapper`)

### Naming Conventions
- **Database Models**: `*Entity` suffix (e.g., `UserEntity`)
- **Pydantic Models**: No suffix for read models, `*Create`/`*Update` for operations
- **Services**: `*Service` (e.g., `UserService`)
- **Data Services**: `*DataService` (e.g., `UserDataService`)

### Code Formatting
- Line length: 119 characters
- Black for formatting, isort for imports (black-compatible profile)
- flake8 ignores: E266, W503, E712, E731, E231
- Max cyclomatic complexity: 18

## Important Implementation Details

### Pagination & Filtering
All list endpoints support:
- `pageNumber` (1-indexed), `pageSize` - Standard pagination
- `omitPagination=true` - Return all results without pagination
- `sortBy` (camelCase field name), `sortDirection` (ascending/descending)
- Custom filters via `Filter` abstraction in `src/data_services/filters.py`

### Camel Case Serialization
- Python code uses `snake_case`
- JSON API uses `camelCase` (automatic via Pydantic alias_generator)
- Sort fields in API use camelCase, converted to snake_case by CRUD layer

### Transaction Management
- **DO NOT** manually call `session.commit()` or `session.rollback()`
- Transactions are managed by `get_db()` context manager
- CRUD layer uses `session.flush()` to persist within transaction
- Router dependency injection handles commit/rollback automatically

### Unique Constraint Violations
Service layer catches `CrudUniqueValidationError` and returns `ErrorStatus.CONFLICT`:
- Override `CREATE_UNIQUE_VALIDATION_MSG` and `UPDATE_UNIQUE_VALIDATION_MSG` in service classes
- Error messages are built dynamically using `build_*_crud_unique_validation_error_msg()` methods

### Testing Strategy
- Tests use mocked `Session` objects (see `src/tests/conftest.py`)
- Fixtures in `src/tests/fixtures/` provide reusable test data
- Use `pytest-mock` for mocking service/data service dependencies
- Never use real database connections in unit tests
