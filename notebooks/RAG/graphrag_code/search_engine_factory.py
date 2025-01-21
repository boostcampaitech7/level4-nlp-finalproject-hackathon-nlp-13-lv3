# search_engine_factory.py
from graphrag.query.structured_search.local_search.search import LocalSearch

def create_search_engine(
    llm,
    context_builder,
    token_encoder,
    llm_params: dict,
    context_builder_params: dict,
    response_type: str = "multiple paragraphs"
) -> LocalSearch:
    """
    LocalSearch 객체를 생성해 반환
    """
    return LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=context_builder_params,
        response_type=response_type,
    )
