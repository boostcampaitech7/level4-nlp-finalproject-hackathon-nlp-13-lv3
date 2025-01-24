from fastapi import FastAPI, HTTPException, Query
from typing import List
from src.vectorizer import create_faiss_index
from src.search import search_faiss
from pydantic import BaseModel

app = FastAPI()

# 검색 결과의 반환 모델 정의
class SearchResult(BaseModel):
    rank: int
    document_id: int
    distance: float
    content: str

# 헬스체크 엔드포인트
@app.get("/")
def home():
    return {"message": "FAISS 검색 시스템이 정상적으로 실행 중입니다."}

# FAISS 인덱스 생성 엔드포인트
@app.post("/index")
def index_documents():
    """FAISS 인덱스를 생성하는 API"""
    create_faiss_index()
    return {"message": "FAISS 인덱스 생성 완료"}

# 검색 엔드포인트
@app.get("/search", response_model=List[SearchResult])
def search_documents(query: str = Query(..., description="검색어를 입력하세요")):
    """쿼리 기반 문서 검색 API"""
    if not query:
        raise HTTPException(status_code=400, detail="검색어를 입력해야 합니다.")

    results = search_faiss(query)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8060)
