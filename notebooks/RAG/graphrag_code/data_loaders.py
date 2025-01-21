# data_loaders.py
import pandas as pd
from typing import Tuple

from graphrag.query.indexer_adapters import (
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)

from config import (
    INPUT_DIR,
    COMMUNITY_REPORT_TABLE,
    ENTITY_TABLE,
    ENTITY_EMBEDDING_TABLE,
    RELATIONSHIP_TABLE,
    TEXT_UNIT_TABLE,
    COMMUNITY_LEVEL,
)


def load_entity_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    엔티티 및 엔티티 임베딩 테이블의 Parquet을 읽어온 뒤 DataFrame으로 반환
    """
    entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet")
    return entity_df, entity_embedding_df


def get_entities(entity_df: pd.DataFrame,
                 entity_embedding_df: pd.DataFrame) -> dict:
    """
    엔티티 DF와 엔티티 임베딩 DF로부터 엔티티 정보를 생성해 반환
    """
    return read_indexer_entities(entity_df, entity_embedding_df, COMMUNITY_LEVEL)


def get_relationships() -> dict:
    """
    관계(relationship) 정보를 담은 DF를 로드하고, 관계 정보를 반환
    """
    relationship_df = pd.read_parquet(f"{INPUT_DIR}/{RELATIONSHIP_TABLE}.parquet")
    return read_indexer_relationships(relationship_df)


def get_reports(entity_df: pd.DataFrame) -> dict:
    """
    커뮤니티 리포트(Community Reports)를 담은 DF를 로드하고, 리포트 정보를 반환
    """
    report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
    return read_indexer_reports(report_df, entity_df, COMMUNITY_LEVEL)


def get_text_units() -> dict:
    """
    텍스트 유닛(Text Units) 정보를 로드하고 반환
    """
    text_unit_df = pd.read_parquet(f"{INPUT_DIR}/{TEXT_UNIT_TABLE}.parquet")
    return read_indexer_text_units(text_unit_df)
