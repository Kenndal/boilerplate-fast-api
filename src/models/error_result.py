from pydantic import BaseModel

from src.models.enums.error_status import ErrorStatus


class ErrorResult(BaseModel):
    status: ErrorStatus
    details: str
