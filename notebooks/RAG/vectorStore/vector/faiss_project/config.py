import os
from pydantic_settings import BaseSettings, SettingsConfigDict

MODE = os.getenv("MODE", "development")


class Settings(BaseSettings):
    MODE: str = "development"
    LOG_PATH: str = "./data/app.log"
    FAISS_INDEX_FOLDER_PATH: str = "data/faiss_index"
    FAISS_DIMENSION: int = 384
    TOP_K_RESULTS: int = 5
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    PICKLE_FILE_PATH: str = "data/documents.pkl"
    API_KEY: str = ''
    model_config = SettingsConfigDict(env_file='./env/.env')


settings = Settings()
