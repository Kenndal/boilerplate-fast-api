from dataclasses import dataclass
import logging
from typing import Any, Protocol, Sequence, Type, cast
from uuid import UUID

import psycopg2
from pydantic import BaseModel
from pydantic.alias_generators import to_snake
from sqlalchemy import Delete, Exists, Select, asc, delete, desc, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session

from src.constants import DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE
from src.data_services.filters import Filter
from src.models.enums.sort_direction import SortDirection
from src.utils.exceptions import CrudException, CrudIntegrityError, CrudUniqueValidationError

logger = logging.getLogger(__name__)


def calculate_offset(page_number: int, page_size: int) -> int:
    return (page_number - 1) * page_size


class ModelToEntityMapper[EntityType: DeclarativeBase, CreateModel: BaseModel](Protocol):
    def __call__(self, model: CreateModel, user_id: str, *args: Any, **kwargs: Any) -> EntityType:
        # Forcing new line with this comment.
        ...


@dataclass
class Crud[Entity: DeclarativeBase, CreateModel: BaseModel, UpdateModel: BaseModel]:
    session: Session
    entity_type: Type[Entity]

    @property
    def _entity_name(self) -> Any:
        return self.entity_type.__name__

    def entity_exists(self, entity_id: UUID) -> bool:
        try:
            stmt = select(exists().where(self.entity_type.id == entity_id))  # type: ignore[attr-defined]
            return bool(self.session.execute(stmt).unique().scalar())
        except Exception as e:
            error_msg = f"Failed to check if entity {self._entity_name} with id {entity_id} exists"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def condition_exists(self, filters: Sequence[Filter]) -> bool:
        try:
            exists_stmt = exists()
            for f in filters:
                exists_stmt = cast(Exists, f.apply(exists_stmt))
            stmt = select(exists_stmt)
            return bool(self.session.execute(stmt).unique().scalar())
        except Exception as e:
            error_msg = f"Failed to check if entities {self._entity_name} exists for conditions {filters}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def _get_one(self, entity_id: UUID) -> Entity:
        try:
            stmt = select(self.entity_type).where(self.entity_type.id == entity_id)  # type: ignore[attr-defined]
            return self.session.scalars(stmt).unique().one()
        except Exception as e:
            error_msg = f"Failed to retrieve {self._entity_name} with id {entity_id}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def get_by_id(self, entity_id: UUID, with_for_update: bool = False) -> Entity | None:
        try:
            stmt = select(self.entity_type).where(self.entity_type.id == entity_id)  # type: ignore[attr-defined]
            if with_for_update:
                stmt = stmt.with_for_update()
            return self.session.scalars(stmt).unique().first()
        except Exception as e:
            error_msg = f"Failed to retrieve {self._entity_name} with id {entity_id}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def _apply_params(
        self,
        stmt: Select[Any],
        count_stmt: Select[Any],
        page_number: int = DEFAULT_PAGE_NUMBER,
        page_size: int = DEFAULT_PAGE_SIZE,
        omit_pagination: bool = False,
        filters: Sequence[Filter] | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> tuple[Select[Any], Select[Any]]:
        if not omit_pagination:
            offset = calculate_offset(page_number, page_size)
            stmt = stmt.limit(page_size).offset(offset)
        if filters:
            for f in filters:
                stmt = cast(Select[Any], f.apply(stmt))
                count_stmt = cast(Select[Any], f.apply(count_stmt))
        if sort_by and (sort_by_key := getattr(self.entity_type, to_snake(sort_by))):
            sort_dir = desc if sort_direction == SortDirection.descending else asc
            stmt = stmt.order_by(sort_dir(sort_by_key))
        return stmt, count_stmt

    def get_by_page(
        self,
        page_number: int = DEFAULT_PAGE_NUMBER,
        page_size: int = DEFAULT_PAGE_SIZE,
        omit_pagination: bool = False,
        filters: Sequence[Filter] | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> tuple[list[Entity], int]:
        try:
            stmt = select(self.entity_type)
            count_stmt = select(func.count()).select_from(self.entity_type)
            stmt, count_stmt = self._apply_params(
                stmt, count_stmt, page_number, page_size, omit_pagination, filters, sort_by, sort_direction
            )
            return list(self.session.scalars(stmt).unique().all()), self.session.scalar(count_stmt) or 0
        except Exception as e:
            error_msg = (
                f"Failed to retrieve multiple entities {self._entity_name} "
                f"with params: {page_number=}, {page_size=} {omit_pagination=}"
            )
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def _create(
        self,
        create_model: CreateModel,
        mapper: ModelToEntityMapper[Entity, CreateModel],
        user_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Entity:
        new_entity = mapper(model=create_model, user_id=user_id)
        self.session.add(new_entity)
        self.session.flush()
        return new_entity

    def create(
        self, create_model: CreateModel, mapper: ModelToEntityMapper[Entity, CreateModel], user_id: str
    ) -> Entity:
        try:
            return self._create(create_model, mapper, user_id)
        except IntegrityError as e:
            error_msg = (
                f"Failed to create new entity {self._entity_name} with params: {create_model=} due to IntegrityError"
            )
            logger.error(f"{error_msg}, {str(e)}")
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                raise CrudUniqueValidationError(error_msg) from e
            raise CrudIntegrityError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create new entity {self._entity_name} with params: {create_model=}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def _update(self, entity_id: UUID, update_model: UpdateModel, user_id: str, *args: Any, **kwargs: Any) -> Entity:
        stmt = (
            update(self.entity_type)
            .where(self.entity_type.id == entity_id)  # type: ignore[attr-defined]
            .values(last_modified_by_user_id=user_id, **update_model.model_dump(exclude_unset=True))
        )
        self.session.execute(stmt)
        self.session.flush()
        return self._get_one(entity_id)

    def update(self, entity_id: UUID, update_model: UpdateModel, user_id: str) -> Entity:
        try:
            logger.info(f"{update_model.model_dump(exclude_unset=True)=}")
            return self._update(entity_id, update_model, user_id)
        except IntegrityError as e:
            error_msg = (
                f"Failed to update entity {self._entity_name} {entity_id} "
                f"with params: {update_model=} due to IntegrityError"
            )
            logger.error(f"{error_msg}, {str(e)}")
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                raise CrudUniqueValidationError(error_msg) from e
            raise CrudIntegrityError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update entity {self._entity_name} {entity_id} with params: {update_model=}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def delete(self, entity_id: UUID) -> None:
        try:
            stmt = delete(self.entity_type).where(self.entity_type.id == entity_id)  # type: ignore[attr-defined]
            self.session.execute(stmt)
            self.session.flush()
        except Exception as e:
            error_msg = f"Failed to delete entity {self._entity_name} {entity_id}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e

    def condition_delete(self, filters: Sequence[Filter]) -> None:
        try:
            stmt = delete(self.entity_type)
            for f in filters:
                stmt = cast(Delete, f.apply(stmt))
            self.session.execute(stmt)
            self.session.flush()
        except Exception as e:
            error_msg = f"Failed to delete entities {self._entity_name} for conditions {filters}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudException(error_msg) from e
