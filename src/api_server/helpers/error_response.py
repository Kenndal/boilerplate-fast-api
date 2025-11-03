from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult


def http_exception_from_error(error: ErrorResult | None) -> HTTPException:
    if error:
        match error.status:
            case ErrorStatus.NOT_FOUND_ERROR:
                return HTTPException(status_code=HTTP_404_NOT_FOUND, detail=error.details)
            case ErrorStatus.BAD_REQUEST:
                return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error.details)
            case ErrorStatus.CONFLICT:
                return HTTPException(status_code=HTTP_409_CONFLICT, detail=error.details)
            case ErrorStatus.INTERNAL_ERROR:
                return HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error.details)
    return HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown error")
