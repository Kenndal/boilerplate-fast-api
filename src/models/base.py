from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class BaseModelWithConfig(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, str_strip_whitespace=True)


class ModelList[T: BaseModel](BaseModel):
    items: list[T]
    total: int


class BaseAudit(BaseModel):
    created_date: datetime
    last_modified_date: datetime
    created_by_user_id: str
    last_modified_by_user_id: str

    @field_validator("created_date", "last_modified_date")
    def add_missing_timezone(cls, v: datetime) -> datetime:  # noqa: N805
        return v.replace(tzinfo=UTC)
