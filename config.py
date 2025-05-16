from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    whitelist_tables: Optional[List[str]] = None
    query_limit_size: Optional[int] = None
    
    username: str
    password: str
    dsn: str

    class Config:
        env_file = ".env"


settings = Settings()
