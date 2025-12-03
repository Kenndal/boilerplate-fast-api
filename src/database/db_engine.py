from sqlalchemy.ext.asyncio import create_async_engine

from src.config.config import config

engine = create_async_engine(config.DATABASE_URL, pool_pre_ping=True, connect_args={"timeout": 10})
