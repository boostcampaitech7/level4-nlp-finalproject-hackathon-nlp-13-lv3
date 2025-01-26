import faiss
import os
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from config import settings
from src.data_loader import load_documents
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


def search_faiss(index_name: str, query: str, size: int):
    """저장된 FAISS 인덱스를 이용한 검색 및 문서 내용 출력"""
    try:

        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{index_name}.index")
        logger.debug(f"인덱스 경로: {index_path}")

        size = size if size else settings.TOP_K_RESULTS
        logger.debug(f"검색 결과 개수: {size}")

        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="인덱스를 찾을 수 없습니다.")

        # 임베딩 모델 로드
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.debug("임베딩 모델 로드 완료")

        # FAISS 인덱스 로드
        index = faiss.read_index(index_path)
        logger.debug(f"FAISS 인덱스 로드 완료: {index.ntotal} 개의 벡터 포함")

        # 문서 로드
        documents = load_documents()
        logger.debug(f"{len(documents)}개의 문서 로드 완료")

        # 쿼리 임베딩 생성
        query_embedding = model.encode([query], convert_to_numpy=True)
        logger.debug(f"쿼리 임베딩 생성 완료: {query_embedding.shape}")

        if query_embedding.shape[1] != index.d:
            raise HTTPException(
                status_code=400, detail="쿼리 벡터 차원이 인덱스 차원과 일치하지 않습니다.")

        # 검색 수행
        distances, indices = index.search(query_embedding, size)
        logger.debug(f"검색 결과: {indices}")

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(documents):
                doc = documents[idx]
                results.append({
                    "rank": rank + 1,
                    "document_id": int(idx),
                    "distance": float(distances[0][rank]),
                    "content": str(doc.page_content)
                })
            else:
                results.append({
                    "rank": rank + 1,
                    "document_id": int(idx),
                    "distance": float(distances[0][rank]),
                    "content": "유효하지 않은 인덱스"
                })

        return results

    except FileNotFoundError:
        logger.error("인덱스를 찾을 수 없습니다.")
        raise HTTPException(status_code=404, detail="인덱스를 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"서버 내부 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")
