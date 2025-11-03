from typing import Any

from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.models.problem_details import ProblemDetails


def _get_response_model(status_code: int, description: str | None = None) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ProblemDetails,
            "content": {"application/json": {}},
            "description": description,
        }
    }


response_400 = _get_response_model(HTTP_400_BAD_REQUEST)
response_401 = _get_response_model(HTTP_401_UNAUTHORIZED)
response_403 = _get_response_model(HTTP_403_FORBIDDEN)
response_404 = _get_response_model(HTTP_404_NOT_FOUND)
response_409 = _get_response_model(HTTP_409_CONFLICT)
response_422 = _get_response_model(HTTP_422_UNPROCESSABLE_CONTENT)
response_500 = _get_response_model(HTTP_500_INTERNAL_SERVER_ERROR)
