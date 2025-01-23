import faiss
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException
from config import EMBEDDING_MODEL, FAISS_INDEX_PATH, TOP_K_RESULTS
from src.data_loader import load_documents  # 문서 로드 함수 가져오기
import logging

# 로깅 설정
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def search_faiss(query: str):
    """저장된 FAISS 인덱스를 이용한 검색 및 문서 내용 출력"""
    try:
        # 임베딩 모델 로드
        model = SentenceTransformer(EMBEDDING_MODEL)

        # FAISS 인덱스 로드
        index = faiss.read_index(FAISS_INDEX_PATH)

        # 문서 로드
        documents = load_documents()

        # 쿼리 임베딩 생성
        query_embedding = model.encode([query], convert_to_numpy=True)

        # FAISS 검색 수행
        distances, indices = index.search(query_embedding, TOP_K_RESULTS)

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < len(documents):
                doc = documents[idx]
                result = {
                    "rank": rank + 1,
                    "document_id": int(idx),
                    "distance": float(distances[0][rank]),  # JSON 직렬화를 위해 float으로 변환
                    "content": str(doc.page_content)  # JSON 직렬화를 위해 문자열로 변환
                }
                results.append(result)
            else:
                result = {
                    "rank": rank + 1,
                    "document_id": int(idx),
                    "distance": float(distances[0][rank]),
                    "content": "유효하지 않은 인덱스"
                }
                results.append(result)
        return results

    except FileNotFoundError as fnf_error:
        logger.error(f"파일을 찾을 수 없습니다: {fnf_error}")
        raise HTTPException(status_code=500, detail="필요한 파일을 찾을 수 없습니다.")
    except faiss.IOError as faiss_error:
        logger.error(f"FAISS 인덱스 로드 오류: {faiss_error}")
        raise HTTPException(status_code=500, detail="FAISS 인덱스를 로드하는 중 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"예기치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")
