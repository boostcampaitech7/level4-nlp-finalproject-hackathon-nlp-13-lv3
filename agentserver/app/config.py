import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "nlp13 template App"
    debug: bool = True
    LOG_PATH: str = "./app/logs/app.log"
    database_url: str = "postgresql://myuser:boostcamp13@localhost:5432/mydatabase"  

    model_config = SettingsConfigDict(env_file='.env',extra="allow")

settings = Settings()