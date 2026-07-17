from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI App"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Git settings
    REPO_STORAGE_PATH: str = "./repos"

    class Config:
        env_file = ".env"


settings = Settings()
