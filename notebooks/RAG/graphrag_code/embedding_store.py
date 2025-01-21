# embedding_store.py
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from config import LANCEDB_URI

def create_description_embedding_store(collection_name: str = "default-entity-description") -> LanceDBVectorStore:
    """
    LanceDB 기반의 벡터 스토어를 생성하고 연결한 뒤 반환
    """
    description_embedding_store = LanceDBVectorStore(
        collection_name=collection_name
    )
    description_embedding_store.connect(db_uri=LANCEDB_URI)
    return description_embedding_store
