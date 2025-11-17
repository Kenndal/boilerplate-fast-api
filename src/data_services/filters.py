from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import Delete, Exists, Select, or_
from sqlalchemy.orm import Mapped


class Filter(ABC):
    @abstractmethod
    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        raise NotImplementedError


@dataclass
class FieldValueExistsFilter(Filter):
    """
    Filters for records where the specified field has any values (not empty).
    """

    field: Mapped[Any]

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field.any())

    def __repr__(self) -> str:
        return f"length({str(self.field)}) not empty"


@dataclass
class FieldValueNotExistsFilter(Filter):
    """
    Filters for records where the specified field has no values (empty).
    """

    field: Mapped[Any]

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(~self.field.any())

    def __repr__(self) -> str:
        return f"not {self.field}"


@dataclass
class EqualsFilter(Filter):
    """
    Filters for records where the field value equals the specified value.

    SQL equivalent: field = 'value'
    """

    field: Mapped[Any]
    value: Any

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field == self.value)

    def __repr__(self) -> str:
        return f"{str(self.field)} == {self.value}"


@dataclass
class NotEqualsFilter(Filter):
    """
    Filters for records where the field value does not equal the specified value.

    SQL equivalent: field != 'value' OR field <> 'value'
    """

    field: Mapped[Any]
    value: Any

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field != self.value)

    def __repr__(self) -> str:
        return f"{str(self.field)} != {self.value}"


@dataclass
class ContainsFilter(Filter):
    """
    Filters for records where the field contains the specified value.
    Works with string and array fields.

    SQL equivalent: field LIKE '%value%' (for strings) OR 'value' = ANY(field) (for arrays)
    """

    field: Mapped[Any]
    value: Any

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field.contains(self.value))

    def __repr__(self) -> str:
        return f"{self.value} in {str(self.field)}"


@dataclass
class AnyFromListFilter(Filter):
    """
    Filters for records where the array field contains any of the specified values.
    Works only for fields with type ARRAY and PostgreSQL database.

    field: ARRAY[Any]
    value: list[Any] = [x, y, z]
    filter condition = x in field OR y in field OR z in field

    SQL equivalent: field && ARRAY['x', 'y', 'z'] (array overlap operator)
    """

    field: Mapped[Any]
    value: list[Any]

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        conditions = [self.field.any(value) for value in self.value]
        return stmt.where(or_(*conditions))

    def __repr__(self) -> str:
        return " or ".join(f"{v} in {str(self.field)}" for v in self.value)


@dataclass
class RelatedEntityFilter(Filter):
    """
    Filters entities based on their relationship to another entity.
    Matches records where the relationship contains any of the specified entity IDs.

    SQL equivalent:
    EXISTS (SELECT 1 FROM related_table WHERE related_table.parent_id = main_table.id
        AND related_table.id IN ('id1', 'id2', 'id3'))
    """

    field: Mapped[Any]
    related_entity_ids: list[UUID]

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        conditions = [self.field.any(id=related_id) for related_id in self.related_entity_ids]
        return stmt.where(or_(*conditions))

    def __repr__(self) -> str:
        return f"{str(self.field)}.id in {self.related_entity_ids}"


@dataclass
class InFilter(Filter):
    """
    Filters for records where the field value is in the specified list of values.
    SQL equivalent: `field IN (value1, value2, value3)`

    Example: Filter users where status is in ['active', 'pending', 'verified']
    """

    field: Mapped[Any]
    value: list[Any]

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field.in_(self.value))

    def __repr__(self) -> str:
        return f"{str(self.field)} IN {self.value!r}"


@dataclass
class CaseInsensitiveContainsFilter(Filter):
    """
    Filters for records where the field contains the specified value (case-insensitive).
    Uses PostgreSQL's icontains operator for case-insensitive string matching.

    SQL equivalent: LOWER(field) LIKE LOWER('%value%') OR field ILIKE '%value%'
    """

    field: Mapped[Any]
    value: Any

    def apply(self, stmt: Select[Any] | Exists | Delete) -> Select[Any] | Exists | Delete:
        return stmt.where(self.field.icontains(self.value))

    def __repr__(self) -> str:
        return f"{str(self.field)} icontains % {self.value} %"
