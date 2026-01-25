from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import psycopg
from pydantic import BaseModel
import pytest
from pytest_mock import MockerFixture
from sqlalchemy import StaticPool, create_engine, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from src.data_services.crud import Crud
from src.data_services.filters import ContainsFilter, EqualsFilter, NotEqualsFilter
from src.models.enums.sort_direction import SortDirection
from src.utils.exceptions import (
    CrudError,
    CrudIntegrityError,
    CrudUniqueValidationError,
)

ENTITY_ID = uuid4()
ENTITY_NAME = "super_name"


class Base(DeclarativeBase):
    pass


class Entity(Base):
    __tablename__ = "entity"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    base: Mapped[str]
    super_name: Mapped[str]
    index: Mapped[int]
    last_modified_by_user_id: Mapped[str]


class CreateModel(BaseModel):
    base: str
    super_name: str


class UpdateModel(BaseModel):
    base: str | None = None
    super_name: str | None = None


def mapper(model: CreateModel, user_id: str) -> Entity:
    return Entity(
        id=ENTITY_ID,
        base=model.base,
        super_name=model.super_name,
        index=1,
        last_modified_by_user_id=user_id,
    )


def fake_mapper_exception(model: CreateModel, user_id: str) -> Entity:
    raise Exception("error")


def fake_mapper_integrity_error(model: CreateModel, user_id: str) -> Entity:
    raise IntegrityError(statement="", params=[], orig=Exception())


def fake_mapper_unique_violation_error(model: CreateModel, user_id: str) -> Entity:
    raise IntegrityError(statement="", params=[], orig=psycopg.errors.UniqueViolation())


@pytest.fixture(scope="module")
def session_maker() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session(session_maker: sessionmaker[Session]) -> Generator[Session, Any, None]:
    db = None
    try:
        db = session_maker()
        yield db
    finally:
        if db:
            db.close()


@pytest.fixture
def create_model() -> CreateModel:
    return CreateModel(base="base", super_name=ENTITY_NAME)


@pytest.fixture
def update_model() -> UpdateModel:
    return UpdateModel(base="new base")


@pytest.fixture
def entity(create_model: CreateModel, user_id: str) -> Entity:
    return Entity(
        id=ENTITY_ID,
        index=1,
        **create_model.model_dump(),
        last_modified_by_user_id=user_id,
    )


@pytest.fixture
def setup_without_created_entity(session: Session, entity: Entity) -> Generator[None, Any, None]:
    try:
        yield
    finally:
        stmt = delete(Entity)
        session.execute(stmt)
        session.commit()


@pytest.fixture
def setup_with_created_entity(session: Session, entity: Entity, setup_without_created_entity: None) -> None:
    session.add(entity)
    session.commit()
    return


@pytest.fixture
def setup_with_created_multiple_entities(
    session: Session,
    entity: Entity,
    create_model: CreateModel,
    setup_without_created_entity: None,
    user_id: str,
) -> None:
    entities = [entity]
    for i in range(2, 5):
        base, super_name = create_model.model_dump()
        entities.append(
            Entity(
                id=uuid4(),
                index=i,
                base=base,
                super_name=f"{super_name}-{i}",
                last_modified_by_user_id=user_id,
            )
        )
    session.add_all(entities)
    session.commit()
    return


@pytest.fixture
def crud(session: Session) -> Crud[Entity, CreateModel, UpdateModel]:
    return Crud[Entity, CreateModel, UpdateModel](session=session, entity_type=Entity)


def test_entity_exists(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_entity: None,
) -> None:
    # Act
    result = crud.entity_exists(ENTITY_ID)

    # Assert
    assert result is True


def test_entity_exists__not_found(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_without_created_entity: None,
) -> None:
    # Act
    result = crud.entity_exists(ENTITY_ID)

    # Assert
    assert result is False


def test_exists__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.select", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud.entity_exists(ENTITY_ID)

    # Assert
    assert str(e.value) == f"Failed to check if entity Entity with id {ENTITY_ID} exists"


def test_get_one(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_entity: None,
) -> None:
    # Act
    result = crud._get_one(ENTITY_ID)

    # Assert
    assert result == entity


def test_get_one__not_found(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_without_created_entity: None,
) -> None:
    # Act
    with pytest.raises(CrudError) as e:
        crud._get_one(ENTITY_ID)

    # Assert
    assert str(e.value) == f"Failed to retrieve Entity with id {ENTITY_ID}"


def test_get_one__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.select", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud._get_one(ENTITY_ID)

    # Assert
    assert str(e.value) == f"Failed to retrieve Entity with id {ENTITY_ID}"


def test_get_by_id(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_entity: None,
) -> None:
    # Act
    result = crud.get_by_id(ENTITY_ID)

    # Assert
    assert result == entity


def test_get_by_id__not_found(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_without_created_entity: None,
) -> None:
    # Act
    result = crud.get_by_id(ENTITY_ID)

    # Assert
    assert result is None


def test_get_by_id__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.select", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud.get_by_id(ENTITY_ID)

    # Assert
    assert str(e.value) == f"Failed to retrieve Entity with id {ENTITY_ID}"


def test_create(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Act
    result = crud.create(create_model, mapper, fake_user_id)

    # Assert
    assert result.id == ENTITY_ID
    assert result.super_name == create_model.super_name
    assert result.base == create_model.base


def test_create__crud_unique_validation_error(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Act
    with pytest.raises(CrudUniqueValidationError) as e:
        crud.create(create_model, fake_mapper_unique_violation_error, fake_user_id)

    # Assert
    assert str(e.value) == f"Failed to create new entity Entity with params: {create_model=} due to IntegrityError"


def test_create__crud_integrity_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Act
    with pytest.raises(CrudIntegrityError) as e:
        crud.create(create_model, fake_mapper_integrity_error, fake_user_id)

    # Assert
    assert str(e.value) == f"Failed to create new entity Entity with params: {create_model=} due to IntegrityError"


def test_create__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Act
    with pytest.raises(CrudError) as e:
        crud.create(create_model, fake_mapper_exception, fake_user_id)

    # Assert
    assert str(e.value) == f"Failed to create new entity Entity with params: {create_model=}"


def test_update(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    update_model: UpdateModel,
    setup_with_created_entity: None,
    fake_user_id: str,
) -> None:
    # Act
    result = crud.update(ENTITY_ID, update_model, fake_user_id)

    # Assert
    assert result.id == ENTITY_ID
    assert result.base == update_model.base
    assert result.super_name == entity.super_name


def test_update__crud_unique_validation_error(
    crud: Crud[Entity, CreateModel, UpdateModel],
    update_model: UpdateModel,
    mocker: MockerFixture,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Arrange
    mocker.patch(
        "src.data_services.crud.update",
        side_effect=IntegrityError(statement="", params=[], orig=psycopg.errors.UniqueViolation()),
    )

    # Act
    with pytest.raises(CrudIntegrityError) as e:
        crud.update(ENTITY_ID, update_model, fake_user_id)

    # Assert
    assert (
        str(e.value)
        == f"Failed to update entity Entity {ENTITY_ID} with params: {update_model=} due to IntegrityError"
    )


def test_update__crud_integrity_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    update_model: UpdateModel,
    mocker: MockerFixture,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Arrange
    mocker.patch(
        "src.data_services.crud.update",
        side_effect=IntegrityError(statement="", params=[], orig=Exception()),
    )

    # Act
    with pytest.raises(CrudIntegrityError) as e:
        crud.update(ENTITY_ID, update_model, fake_user_id)

    # Assert
    assert (
        str(e.value)
        == f"Failed to update entity Entity {ENTITY_ID} with params: {update_model=} due to IntegrityError"
    )


def test_update__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    update_model: UpdateModel,
    mocker: MockerFixture,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.update", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud.update(ENTITY_ID, update_model, fake_user_id)

    # Assert
    assert str(e.value) == f"Failed to update entity Entity {ENTITY_ID} with params: {update_model=}"


def test_delete(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_entity: None,
) -> None:
    # Act
    crud.delete(ENTITY_ID)
    result = crud.get_by_id(ENTITY_ID)

    # Assert
    assert result is None


def test_delete__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.delete", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud.delete(ENTITY_ID)

    # Assert
    assert str(e.value) == f"Failed to delete entity Entity {ENTITY_ID}"


@pytest.mark.parametrize(("base", "expected_total"), [("base", 0), ("ENTITY_NAME", 4)])
def test_condition_delete(
    crud: Crud[Entity, CreateModel, UpdateModel],
    setup_with_created_multiple_entities: None,
    base: str,
    expected_total: bool,
) -> None:
    # Arrange
    f = EqualsFilter(Entity.base, base)

    # Act
    crud.condition_delete(filters=[f])
    _, total = crud.get_by_page(omit_pagination=True)

    # Assert
    assert total is expected_total


def test_condition_delete__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.delete", side_effect=CrudError("error"))
    f = EqualsFilter(Entity.base, "base")
    f2 = NotEqualsFilter(Entity.super_name, "super_name")

    # Act
    with pytest.raises(CrudError) as e:
        crud.condition_delete(filters=[f, f2])

    # Assert
    assert (
        str(e.value)
        == "Failed to delete entities Entity for conditions [Entity.base == base, Entity.super_name != super_name]"
    )


def test_get_by_page(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_entity: None,
) -> None:
    # Act
    result, total = crud.get_by_page()

    # Assert
    assert result == [entity]
    assert total == 1


@pytest.mark.parametrize(
    ("page_number", "page_size", "omit_pagination", "expected_count"),
    [(1, 1, False, 1), (1, 2, False, 2), (1, 1, True, 4)],
)
def test_get_by_page__params(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_multiple_entities: None,
    page_number: int,
    page_size: int,
    omit_pagination: bool,
    expected_count: int,
) -> None:
    # Act
    result, total = crud.get_by_page(page_number, page_size, omit_pagination)

    # Assert
    assert len(result) == expected_count
    assert total == 4


def test_get_by_page__page_number(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_multiple_entities: None,
) -> None:
    # Act
    result, total = crud.get_by_page(4, 1)

    # Assert
    assert len(result) == 1
    assert result[0].index == 4
    assert total == 4


def test_get_by_page__with_equals_filter(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_multiple_entities: None,
) -> None:
    # Arrange
    f = EqualsFilter(Entity.id, ENTITY_ID)

    # Act
    result, total = crud.get_by_page(filters=[f])

    # Assert
    assert result == [entity]
    assert total == 1


def test_get_by_page__with_not_equals_filter(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_without_created_entity: None,
    fake_user_id: str,
) -> None:
    # Arrange
    crud.create(create_model, mapper, fake_user_id)
    f = NotEqualsFilter(Entity.id, ENTITY_ID)

    # Act
    result, total = crud.get_by_page(filters=[f])

    # Assert
    assert result == []
    assert total == 0


def test_get_by_page__with_contains_filter(
    crud: Crud[Entity, CreateModel, UpdateModel],
    create_model: CreateModel,
    setup_with_created_multiple_entities: None,
) -> None:
    # Arrange
    f = ContainsFilter(Entity.super_name, "super_name-")

    # Act
    result, total = crud.get_by_page(filters=[f])

    # Assert
    assert len(result) == 3
    assert total == 3


@pytest.mark.parametrize(
    ("sort_by", "sort_direction", "expected_result"),
    [
        (
            "super_name",
            SortDirection.descending,
            ["super_name-4", "super_name-3", "super_name-2", "super_name"],
        ),
        (
            "superName",
            SortDirection.descending,
            ["super_name-4", "super_name-3", "super_name-2", "super_name"],
        ),
        (
            "super-name",
            SortDirection.descending,
            ["super_name-4", "super_name-3", "super_name-2", "super_name"],
        ),
        (
            "SuperName",
            SortDirection.descending,
            ["super_name-4", "super_name-3", "super_name-2", "super_name"],
        ),
        (
            "super_name",
            SortDirection.ascending,
            ["super_name", "super_name-2", "super_name-3", "super_name-4"],
        ),
    ],
)
def test_get_by_page__with_sorting(
    crud: Crud[Entity, CreateModel, UpdateModel],
    entity: Entity,
    setup_with_created_multiple_entities: None,
    sort_by: str,
    sort_direction: SortDirection,
    expected_result: list[str],
) -> None:
    # Act
    result, total = crud.get_by_page(sort_by=sort_by, sort_direction=sort_direction)

    sorted_result = [entity.super_name for entity in result]

    # Assert
    assert sorted_result == expected_result
    assert total == 4


def test_get_by_page__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.select", side_effect=CrudError("error"))

    # Act
    with pytest.raises(CrudError) as e:
        crud.get_by_page()

    # Assert
    assert str(e.value) == (
        "Failed to retrieve multiple entities Entity with params: page_number=1, page_size=10 omit_pagination=False"
    )


@pytest.mark.parametrize(("super_name", "expected_result"), [(ENTITY_NAME, True), ("ENTITY_NAME", False)])
def test_condition_exists(
    crud: Crud[Entity, CreateModel, UpdateModel],
    setup_with_created_multiple_entities: None,
    super_name: str,
    expected_result: bool,
) -> None:
    # Arrange
    f = EqualsFilter(Entity.super_name, super_name)

    # Act
    result = crud.condition_exists(filters=[f])

    # Assert
    assert result is expected_result


def test_condition_exists__crud_exception(
    crud: Crud[Entity, CreateModel, UpdateModel],
    mocker: MockerFixture,
    setup_without_created_entity: None,
) -> None:
    # Arrange
    mocker.patch("src.data_services.crud.exists", side_effect=CrudError("error"))
    f = EqualsFilter(Entity.base, "base")
    f2 = NotEqualsFilter(Entity.super_name, "super_name")

    # Act
    with pytest.raises(CrudError) as e:
        crud.condition_exists(filters=[f, f2])

    # Assert
    assert (
        str(e.value) == "Failed to check if entities Entity exists for conditions "
        "[Entity.base == base, Entity.super_name != super_name]"
    )
