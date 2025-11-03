from sqlalchemy.orm import Session

from src.data_services.crud import Crud
from src.database.entities.user import UserEntity
from src.models.user import UserCreate, UserUpdate


class UserDataService(Crud[UserEntity, UserCreate, UserUpdate]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session=session,
            entity_type=UserEntity,
        )
