from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.api_server.main import app
from src.data_services.user_data_service import UserDataService
from src.models.base import BaseAudit
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.user_service import UserService

pytest_plugins = [
    "src.tests.fixtures.user_fixtures",
]


@pytest.fixture(scope="session")
def user_id() -> str:
    return str(uuid4())


@pytest.fixture(scope="session")
def fake_user_id() -> str:
    return "fake_user_id"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def audit(user_id: str) -> BaseAudit:
    now = datetime.now(tz=UTC)
    return BaseAudit(
        created_date=now, last_modified_date=now, created_by_user_id=user_id, last_modified_by_user_id=user_id
    )


@pytest.fixture
def session(mocker: MockerFixture) -> Session:
    return cast(Session, mocker.MagicMock())


@pytest.fixture
def user_data_service(session: Session) -> UserDataService:
    return UserDataService(session=session)


@pytest.fixture
def user_service(user_data_service: UserDataService) -> UserService:
    return UserService(data_service=user_data_service)


@pytest.fixture
def error_result_internal_error() -> ErrorResult:
    return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="error")
