# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터가 저장된 경로
INPUT_DIR = "./ragtest/output"
LANCEDB_URI = f"{INPUT_DIR}/lancedb"

# 테이블(혹은 파일)명 상수
COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"
ENTITY_EMBEDDING_TABLE = "create_final_entities"
RELATIONSHIP_TABLE = "create_final_relationships"
COVARIATE_TABLE = "create_final_covariates"
TEXT_UNIT_TABLE = "create_final_text_units"

# 특정 그래프/네트워크 수준
COMMUNITY_LEVEL = 2

# 환경 변수에서 API 키와 모델 이름 불러오기
API_KEY = os.getenv("GRAPHRAG_API_KEY")
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
