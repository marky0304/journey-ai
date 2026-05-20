from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner"
    redis_url: str = "redis://localhost:6379/0"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    seniverse_api_key: str = ""
    amap_api_key: str = ""
    jwt_secret_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
