from uuid import UUID, uuid4

import pytest
from starlette.status import HTTP_404_NOT_FOUND

from src.database.entities.user import UserEntity
from src.models.base import BaseAudit, ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.user import User, UserCreate, UserUpdate


@pytest.fixture(scope="module")
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def user_create() -> UserCreate:
    return UserCreate(
        first_name="John", last_name="Doe", username="johndoe", email="john.doe@example.com", is_active=True
    )


@pytest.fixture
def user_update() -> UserUpdate:
    return UserUpdate(
        first_name="Jane", last_name="Smith", username="janesmith", email="jane.smith@example.com", is_active=False
    )


@pytest.fixture
def user(user_id: UUID, user_create: UserCreate, audit: BaseAudit) -> User:
    return User(id=user_id, **user_create.model_dump(), **audit.model_dump())


@pytest.fixture
def users(user: User) -> ModelList[User]:
    return ModelList[User](items=[user], total=1)


@pytest.fixture
def user_entity(user: User) -> UserEntity:
    return UserEntity(**user.model_dump())


@pytest.fixture
def user_error_result_not_found(user_id: UUID) -> ErrorResult:
    return ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details=f"User with id {user_id} not found")


@pytest.fixture
def user_not_found(user_error_result_not_found: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        title="Not Found",
        detail=user_error_result_not_found.details,
        status=HTTP_404_NOT_FOUND,
    )


@pytest.fixture
def user_error_result_already_exists() -> ErrorResult:
    return ErrorResult(status=ErrorStatus.CONFLICT, details="User already exists")


@pytest.fixture
def user_already_exists(user_error_result_already_exists: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        title="Conflict",
        detail=user_error_result_already_exists.details,
        status=409,
    )
