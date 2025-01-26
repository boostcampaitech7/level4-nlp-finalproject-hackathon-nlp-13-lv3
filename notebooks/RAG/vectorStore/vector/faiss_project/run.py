from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import logging
import uvicorn
import os
import faiss
import numpy as np
import argparse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import traceback

from src.data_loader import load_documents
from src.vectorizer import create_faiss_index
from src.search import search_faiss
from config import settings
from typing import List
from sentence_transformers import SentenceTransformer

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_PATH),  # 로그를 파일로 저장출력
        logging.StreamHandler(),        # 콘솔에도
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 요청 데이터 모델 정의
class IndexCreateRequest(BaseModel):
    index: str
    algorithm: int = 1  # 기본값: Flat
    dimension: int = settings.FAISS_DIMENSION  # 기본값: 768


class DataInsertRequest(BaseModel):
    index: str
    input_vector: List[float]  # 벡터화된 데이터 (리스트 형태)

class QueryRequest(BaseModel):
    index: str
    query: str  # 검색할 텍스트 (쿼리)
    size: int = settings.TOP_K_RESULTS  # 기본값: 5


class VectorQueryRequest(BaseModel):
    size: int = settings.TOP_K_RESULTS  # 기본값: 5
    index: str
    query_vector: List[float]  # 검색할 벡터 (리스트 형태)
    size: int = settings.TOP_K_RESULTS  # 기본값: 5


# 임베딩 모델 로드
model = SentenceTransformer(settings.EMBEDDING_MODEL)


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger_name = f"API {request.method.upper()} {request.url.path}"
        request.state.logger = logging.getLogger(logger_name)
        response = await call_next(request)
        return response


app.add_middleware(LoggerMiddleware)


@app.post("/api/index")
def create_index(request: IndexCreateRequest, request_obj: Request):
    """
    FAISS 인덱스를 생성하는 API 엔드포인트.
    """
    logger = request_obj.state.logger
    try:
        logger.info(
            f"FAISS 인덱스 생성 요청: {request.index}, 알고리즘: {request.algorithm} 차원 수 {request.dimension}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{request.index}.index")

        # 이미 인덱스가 존재하는지 확인
        if os.path.exists(index_path):
            logger.error("현재 같은 인덱스가 존재합니다.")
            raise HTTPException(status_code=400, detail="현재 같은 인덱스가 존재합니다.")

        # FAISS 인덱스 생성
        success, message = create_faiss_index(
            request.index, request.algorithm, request.dimension)

        if not success:
            logger.error(f"인덱스 생성 실패: {message}")
            raise HTTPException(status_code=400, detail=message)

        return {"status": "ok", "message": "인덱스를 생성하였습니다", "index": request.index}

    except Exception as e:
        logger.error(f"서버 내부 오류: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")


@app.get("/api/index")
def check_index_exists(index: str, request_obj: Request):
    """
    FAISS 인덱스가 존재하는지 확인하는 API 엔드포인트.
    """
    try:
        logger = request_obj.state.logger
        logger.info(f"인덱스 조회 요청: {index}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{index}.index")

        if os.path.exists(index_path):
            return {"status": "ok", "message": "해당 인덱스가 존재합니다.", "index": index}
        else:
            return {"status": "ok", "message": "해당 인덱스가 존재하지 않습니다.", "index": index}

    except Exception as e:
        logger.error(f"서버 내부 오류: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"에러가 발생하였습니다 -> {str(e)}")


@app.delete("/api/index")
def delete_index(index: str, request_obj: Request):
    """
    FAISS 인덱스를 삭제하는 API 엔드포인트.
    """
    logger = request_obj.state.logger
    try:
        logger.info(f"인덱스 삭제 요청: {index}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{index}.index")

        if os.path.exists(index_path):
            os.remove(index_path)
            return {"status": "ok", "message": "인덱스를 삭제하였습니다.", "index": index}
        else:
            return {"status": "ok", "message": "삭제하지 못 하였습니다 (인덱스가 존재하지 않음).", "index": index}

    except Exception as e:
        logger.error(f"서버 내부 오류: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"에러가 발생하였습니다 -> {str(e)}")


@app.post("/api/context")
def insert_data(request: DataInsertRequest, request_obj: Request):
    """
    벡터화된 데이터를 FAISS 인덱스에 삽입하는 API 엔드포인트.
    """
    logger = request_obj.state.logger
    try:
        logger.info(f"데이터 삽입 요청 - 인덱스: {request.index}, 벡터 크기: {len(request.input_vector)}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{request.index}.index")

        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="인덱스가 존재하지 않습니다.")

        # FAISS 인덱스 로드
        index = faiss.read_index(index_path)

        # 데이터 삽입
        input_vector = np.array(request.input_vector, dtype=np.float32).reshape(1, -1)  # 벡터 크기 조정
        index.add(input_vector)  # 벡터 삽입

        # 인덱스 업데이트 후 저장
        faiss.write_index(index, index_path)

        return {"status": "ok", "message": "데이터 삽입에 성공하였습니다."}

    except Exception as e:
        logger.error(f"데이터 삽입 실패: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="데이터 삽입에 실패하였습니다.")


@app.post("/api/context/search-by-query")
def search_by_query(request: QueryRequest, request_obj: Request):
    """
    검색어를 벡터화하여 데이터를 검색하는 API 엔드포인트.
    """
    logger = request_obj.state.logger
    try:
        logger.info(
            f"검색어로 쿼리 조회 요청 - 인덱스: {request.index}, 검색어: {request.query}, 요청 개수: {request.size}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{request.index}.index")

        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="인덱스가 존재하지 않습니다.")
        top_k_size = request.size if request.size else settings.TOP_K_RESULTS
        # FAISS 인덱스 로드
        index = faiss.read_index(index_path)

        # 검색어를 벡터로 변환
        query_vector = model.encode([request.query], convert_to_numpy=True)

        # 검색
        distances, indices = index.search(query_vector, top_k_size)

        # 문서 로드 (load_documents()가 문서 데이터를 반환한다고 가정)
        documents = load_documents()  # 문서 로드 함수는 이미 구현되어 있어야 합니다.

        # 결과 반환 (문서 내용도 함께 반환)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(documents):  # 유효한 인덱스일 경우
                doc = documents[idx]  # 문서 객체 가져오기
                results.append({
                    "document_id": int(idx),
                    "distance": float(dist),
                    "content": doc.page_content  # 문서 내용 추가
                })
            else:
                results.append({
                    "document_id": int(idx),
                    "distance": float(dist),
                    "content": "문서 내용 없음"  # 잘못된 인덱스에 대한 처리
                })

        return {"status": "ok", "results": results}

    except Exception as e:
        logger.error(f"쿼리 조회 실패: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="쿼리 조회에 실패하였습니다.")



@app.post("/api/context/search-by-vector")
def search_by_vector(request: VectorQueryRequest, request_obj: Request):
    """
    벡터를 이용하여 데이터를 검색하는 API 엔드포인트.
    """
    logger = request_obj.state.logger
    try:
        logger.info(
            f"벡터로 쿼리 조회 요청 - 인덱스: {request.index}, 벡터 크기: {len(request.query_vector)}, 요청 개수: {request.size}")

        # 인덱스 파일 경로
        index_path = os.path.join(
            settings.FAISS_INDEX_FOLDER_PATH, f"{request.index}.index")

        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="인덱스가 존재하지 않습니다.")
        top_k_size = request.size if request.size else settings.TOP_K_RESULTS

        # FAISS 인덱스 로드
        index = faiss.read_index(index_path)

        # 쿼리 벡터
        query_vector = np.array(request.query_vector, dtype=np.float32).reshape(1, -1)

        # 검색
        distances, indices = index.search(query_vector, top_k_size)

        # 결과 반환
        results = [{"document_id": int(idx), "distance": float(dist)} for idx, dist in zip(indices[0], distances[0])]

        return {"status": "ok", "results": results}

    except Exception as e:
        logger.error(f"벡터 조회 실패: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="벡터 조회에 실패하였습니다.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8060)
