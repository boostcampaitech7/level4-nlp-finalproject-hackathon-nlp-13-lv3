import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "nlp13 template App"
    debug: bool = True
    LOG_PATH: str = "./app/logs/app.log"
    database_url: str = ""  # 필요에 따라 다른 DB URL로 변경
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    REDIRECT_URI: str = ""
    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
