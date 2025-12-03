from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_services.user_data_service import UserDataService
from src.database.db_engine import engine
from src.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(bind=engine, autoflush=False, autocommit=False) as session:
        async with session.begin():
            yield session


async def get_user_data_service(db_session: AsyncSession = Depends(get_db)) -> UserDataService:
    return UserDataService(session=db_session)


async def get_user_service(user_data_service: UserDataService = Depends(get_user_data_service)) -> UserService:
    return UserService(data_service=user_data_service)
