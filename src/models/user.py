from uuid import UUID

from pydantic import ConfigDict

from src.models.base import BaseAudit, BaseModelWithConfig


class UserCreate(BaseModelWithConfig):
    first_name: str
    last_name: str
    username: str
    email: str
    is_active: bool = True


class UserUpdate(BaseModelWithConfig):
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    email: str = ""
    is_active: bool = True


class User(UserCreate, BaseAudit):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
