from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODE: str = "development"
    LOG_PATH: str = "./data/app.log"
    FAISS_INDEX_FOLDER_PATH: str = "data/faiss_index"
    FAISS_DIMENSION: int = 384
    TOP_K_RESULTS: int = 5
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    PICKLE_FILE_PATH: str = "data/documents.pkl"

    model_config = SettingsConfigDict(env_file='.env')

    def model_post_init(self, __context):
        if self.MODE == "development":
            self.LOG_PATH = "data/app.log"
            self.FAISS_INDEX_FOLDER_PATH = "data/faiss_index"
            self.PICKLE_FILE_PATH = "data/documents.pkl"
        else:
            self.LOG_PATH = "/data/app.log"
            self.FAISS_INDEX_FOLDER_PATH = "/data/faiss_index"
            self.PICKLE_FILE_PATH = "/data/documents.pkl"


settings = Settings()
