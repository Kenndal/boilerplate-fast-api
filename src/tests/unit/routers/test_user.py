from unittest.mock import AsyncMock
from uuid import UUID

from httpx import AsyncClient
import pytest
from pytest_mock import MockerFixture
from result import Err, Ok
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from src.constants import USER_PREFIX, VERSION_PREFIX
from src.models.base import ModelList
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.user import User, UserCreate, UserUpdate
from src.services.user_service import UserService
from src.tests.utils import is_expected_result_json

USER_URL = f"/{VERSION_PREFIX}/{USER_PREFIX}"


@pytest.mark.asyncio
async def test_get_users(client: AsyncClient, users: ModelList[User], mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_page",
        new=AsyncMock(return_value=Ok(users)),
    )

    # Act
    response = await client.get(USER_URL)

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), users)


@pytest.mark.asyncio
async def test_get_users__validation_error(client: AsyncClient) -> None:
    # Act
    response = await client.get(f"{USER_URL}?pageNumber=True&pageSize=kek&omitPagination=2&sortBy=name")

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_user_by_id(
    client: AsyncClient,
    user_id: UUID,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_by_id",
        new=AsyncMock(return_value=Ok(user)),
    )

    # Act
    response = await client.get(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), user)


@pytest.mark.asyncio
async def test_get_user_by_id__user_not_found(
    client: AsyncClient,
    user_error_result_not_found: ErrorResult,
    user_id: UUID,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_by_id",
        new=AsyncMock(return_value=Err(user_error_result_not_found)),
    )

    # Act
    response = await client.get(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)


@pytest.mark.asyncio
async def test_create_user(
    client: AsyncClient,
    user_create: UserCreate,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserService, "create", new=AsyncMock(return_value=Ok(user)))

    # Act
    response = await client.post(USER_URL, json=user_create.model_dump())

    # Assert
    assert response.status_code == HTTP_201_CREATED
    assert is_expected_result_json(response.json(), user)


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::UserWarning")
async def test_create_user__validation_error(client: AsyncClient, user_create: UserCreate) -> None:
    # Arrange
    user_create.first_name = 1  # type: ignore[assignment]

    # Act
    response = await client.post(USER_URL, json=user_create.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_user(
    client: AsyncClient, user_id: UUID, user_update: UserUpdate, user: User, mocker: MockerFixture
) -> None:
    # Arrange
    mocker.patch.object(UserService, "update", new=AsyncMock(return_value=Ok(user)))

    # Act
    response = await client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), user)


@pytest.mark.asyncio
async def test_update_user__user_not_found(
    client: AsyncClient,
    user_id: UUID,
    user_update: UserUpdate,
    user_error_result_not_found: ErrorResult,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserService, "update", new=AsyncMock(return_value=Err(user_error_result_not_found)))

    # Act
    response = await client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::UserWarning")
async def test_update_user__validation_error(client: AsyncClient, user_id: UUID, user_update: UserUpdate) -> None:
    # Arrange
    user_update.first_name = 1  # type: ignore[assignment]

    # Act
    response = await client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, user_id: UUID, mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "delete",
        new=AsyncMock(return_value=Ok(None)),
    )
    # Act
    response = await client.delete(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_user__user_not_found(
    client: AsyncClient,
    user_id: UUID,
    user_error_result_not_found: ErrorResult,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "delete",
        new=AsyncMock(return_value=Err(user_error_result_not_found)),
    )

    # Act
    response = await client.delete(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)
