# context_builder.py
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey

def create_local_search_context(
    community_reports: dict,
    text_units: dict,
    entities: dict,
    relationships: dict,
    description_embedding_store,
    text_embedder,
    token_encoder
) -> LocalSearchMixedContext:
    """
    LocalSearchMixedContext를 생성해 반환
    """
    return LocalSearchMixedContext(
        community_reports=community_reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        entity_text_embeddings=description_embedding_store,
        embedding_vectorstore_key=EntityVectorStoreKey.ID,  # 필요에 따라 .TITLE 로 변경
        text_embedder=text_embedder,
        token_encoder=token_encoder
    )
