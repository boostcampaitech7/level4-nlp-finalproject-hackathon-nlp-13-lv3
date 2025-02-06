"""
FastAPI 서버 진입점
- 서버 초기화 및 라우터 등록
"""

from fastapi import FastAPI
from .api.routes import router

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
