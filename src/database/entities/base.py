from datetime import UTC, datetime
from functools import partial

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config.config import config

utc_now = partial(datetime.now, tz=UTC)


class Base(DeclarativeBase):
    metadata = MetaData(schema=config.DATABASE_SCHEMA)


class BaseAuditEntity:
    created_date: Mapped[datetime] = mapped_column(default=utc_now)
    last_modified_date: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)
    created_by_user_id: Mapped[str]
    last_modified_by_user_id: Mapped[str]
    is_active: Mapped[bool]
