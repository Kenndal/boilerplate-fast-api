from sqlalchemy import create_engine

from src.config.config import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
