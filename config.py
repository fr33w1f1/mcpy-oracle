from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Literal

class Settings(BaseSettings):
    whitelist_tables: Optional[List[str]] = None
    query_limit_size: Optional[int] = None
    cost_threshold: Optional[int] = 200000
    
    username: str
    password: str
    dsn: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
