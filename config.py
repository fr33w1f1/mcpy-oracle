from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    whitelist_tables: Optional[List[str]] = None
    query_limit_size: Optional[int] = None
    
    username: str
    password: str
    dsn: str

    fastmcp_port: Optional[int] = None
    fastmcp_host: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
