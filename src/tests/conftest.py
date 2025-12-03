from datetime import datetime
from typing import Any, AsyncGenerator, cast
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def audit(user_id: str) -> BaseAudit:
    now = datetime.now()
    return BaseAudit(
        created_date=now, last_modified_date=now, created_by_user_id=user_id, last_modified_by_user_id=user_id
    )


@pytest.fixture()
def session(mocker: MockerFixture) -> AsyncSession:
    return cast(AsyncSession, mocker.MagicMock())


@pytest.fixture()
def user_data_service(session: AsyncSession) -> UserDataService:
    return UserDataService(session=session)


@pytest.fixture()
def user_service(user_data_service: UserDataService) -> UserService:
    return UserService(data_service=user_data_service)


@pytest.fixture
def error_result_internal_error() -> ErrorResult:
    return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="error")
