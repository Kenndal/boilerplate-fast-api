from pydantic import computed_field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    IS_PROD: bool = False

    # Database configuration
    DATABASE_USERNAME: str = "db_master_admin"
    DATABASE_PASSWORD: str = "db_master_admin_password"
    DATABASE_HOSTNAME: str = "0.0.0.0"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "app_db"
    DATABASE_SCHEMA: str = "sample_schema"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DATABASE_USERNAME}:"
            f"{self.DATABASE_PASSWORD}@{self.DATABASE_HOSTNAME}:"
            f"{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


config = Config()
