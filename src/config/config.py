from pydantic import computed_field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    IS_PROD: bool = False

    # Database configuration
    DATABASE_USERNAME: str = "db_master_admin"
    DATABASE_PASSWORD: str = "db_master_admin_password"  # noqa: S105
    DATABASE_HOSTNAME: str = "0.0.0.0"  # noqa: S104
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "app_db"
    DATABASE_SCHEMA: str = "sample_schema"

    # Logging configuration
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_LEVEL: str = "INFO"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return (
            f"postgresql+psycopg://{self.DATABASE_USERNAME}:"
            f"{self.DATABASE_PASSWORD}@{self.DATABASE_HOSTNAME}:"
            f"{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


config = Config()
