from typing import Any

from src.models.base import BaseModelWithConfig


class ProblemDetails(BaseModelWithConfig):
    title: str
    detail: str
    instance: str | None = None
    status: int
    type: str = "about:blank"
    additional_properties: dict[str, Any] | None = None
