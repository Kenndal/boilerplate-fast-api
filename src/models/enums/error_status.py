from enum import StrEnum


class ErrorStatus(StrEnum):
    NOT_FOUND_ERROR = "NotFound"
    BAD_REQUEST = "BadRequest"
    CONFLICT = "Conflict"
    INTERNAL_ERROR = "InternalError"
