from collections.abc import Generator
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from src.data_services.user_data_service import UserDataService
from src.database.db_engine import engine
from src.services.user_service import UserService


def get_db() -> Generator[Session, Any, None]:
    with Session(bind=engine, autoflush=False, autocommit=False) as session, session.begin():
        yield session


def get_user_data_service(db_session: Session = Depends(get_db)) -> UserDataService:
    return UserDataService(session=db_session)


def get_user_service(user_data_service: UserDataService = Depends(get_user_data_service)) -> UserService:
    return UserService(data_service=user_data_service)
