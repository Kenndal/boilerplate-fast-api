import uuid

from src.database.entities.user import UserEntity
from src.models.user import UserCreate


def to_user_entity(model: UserCreate, user_id: str) -> UserEntity:
    return UserEntity(
        id=uuid.uuid4(),
        first_name=model.first_name,
        last_name=model.last_name,
        username=model.username,
        email=model.email,
        is_active=model.is_active,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
