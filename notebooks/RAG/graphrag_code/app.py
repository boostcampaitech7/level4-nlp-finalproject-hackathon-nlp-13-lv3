# app.py
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

# 모듈 분리된 파일들 임포트
from data_loaders import (
    load_entity_dataframes,
    get_entities,
    get_relationships,
    get_reports,
    get_text_units
)
from embedding_store import create_description_embedding_store
from llm_factory import create_llm, create_text_embedder, create_token_encoder
from context_builder import create_local_search_context
from search_engine_factory import create_search_engine
from post_process import extract_sources_numbers, filter_text_by_ids
import pandas as pd

# 검색 엔진을 전역(or app state)에 저장할 변수
search_engine = None

app = FastAPI()


class QuestionRequest(BaseModel):
    question: str


@app.on_event("startup")
async def startup_event():
    """
    서버 기동 시 1회만 실행되는 초기화 이벤트 훅.
    여기에 모델이나 검색 엔진 등을 준비해둠.
    """
    global search_engine

    # 1) 데이터 로딩
    entity_df, entity_embedding_df = load_entity_dataframes()
    entities = get_entities(entity_df, entity_embedding_df)
    relationships = get_relationships()
    reports = get_reports(entity_df)
    text_units = get_text_units()

    # 2) 벡터 스토어 연결
    description_embedding_store = create_description_embedding_store()

    # 3) LLM, 임베딩, 토큰 인코더 생성
    llm = create_llm()
    text_embedder = create_text_embedder()
    token_encoder = create_token_encoder()

    # 4) Context Builder 생성
    context_builder = create_local_search_context(
        community_reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        description_embedding_store=description_embedding_store,
        text_embedder=text_embedder,
        token_encoder=token_encoder
    )

    # 5) LocalSearch 엔진 생성
    local_context_params = {
        "text_unit_prop": 0.5,
        "community_prop": 0.1,
        "conversation_history_max_turns": 5,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": 10,
        "top_k_relationships": 10,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": "ID",  # EntityVectorStoreKey.ID
        "max_tokens": 12000,
    }

    llm_params = {
        "max_tokens": 2000,
        "temperature": 0.0,
    }

    search_engine = create_search_engine(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=local_context_params,
        response_type="multiple paragraphs"
    )


@app.post("/ask")
async def ask_question(payload: QuestionRequest):
    """
    질문을 받아서 검색 엔진에 전달 후 결과를 반환
    """
    global search_engine
    if search_engine is None:
        return {"error": "Search engine is not initialized yet."}

    # 실제 검색 실행
    result = await search_engine.asearch(payload.question)

    response = result.response
        
    # 3) 참조 문서 ID 추출
    source_ids = extract_sources_numbers(response)
        
    # 4) context_data['sources']에서 참조 문서 텍스트 필터링
    df_sources = pd.DataFrame(result.context_data['sources'])
        
    if source_ids:
        retrieved_docs = filter_text_by_ids(df_sources, source_ids)
    else:
        retrieved_docs = "답을 추론할 수 있는 문서를 찾지 못하였습니다."
    
    return {
        "reference" : retrieved_docs, 
        "answer": response
        }

