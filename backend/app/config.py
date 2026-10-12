from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    default_servings: int = 4
    bring_email: str = ""
    bring_password: str = ""
    bring_list_uuid: str = ""
    bring_push_password: str = "family"


@lru_cache
def get_settings() -> Settings:
    return Settings()
