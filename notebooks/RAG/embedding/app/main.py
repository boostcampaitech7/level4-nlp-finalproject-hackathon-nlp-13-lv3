from fastapi import FastAPI
from app.routes import router
from app.logger import setup_logger
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Embedding API", description="FastAPI-based embedding server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
setup_logger()

# 라우터 등록
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8060)
