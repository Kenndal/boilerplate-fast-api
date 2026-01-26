from collections.abc import Generator
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from src.data_services.task_data_service import TaskDataService
from src.data_services.user_data_service import UserDataService
from src.database.db_engine import engine
from src.services.task_service import TaskService
from src.services.user_service import UserService


def get_db() -> Generator[Session, Any, None]:
    with Session(bind=engine, autoflush=False, autocommit=False) as session, session.begin():
        yield session
