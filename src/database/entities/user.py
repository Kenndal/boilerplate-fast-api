from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from src.database.entities.base import Base, BaseAuditEntity


class UserEntity(Base, BaseAuditEntity):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
