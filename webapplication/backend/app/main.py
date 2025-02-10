# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import argparse

from app.api.router import api_router
from app.config import settings
from app.db.session import init_db
from app.logging import logger
from app.middleware import LoggerMiddleware
# API Key 인증(VPN 환경에서는 불필요하므로 주석 처리)

# API_KEY_NAME = "x-api-key"
# API_KEY = settings.API_KEY  # 실제 API Key로 대체

# api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# async def get_api_key(
#     api_key_header: str = Security(api_key_header),
# ):
#     if api_key_header == API_KEY:
#         return api_key_header
#     else:
#         raise HTTPException(
#             status_code=403, detail="Could not validate credentials"
#         )

# app = FastAPI(dependencies=[Depends(get_api_key)])
0

app = FastAPI(title=settings.app_name, debug=settings.debug,
              docs_url="/api-docs", redoc_url="/api-redoc", openapi_url="/api-schema.json")

# CORS 미들웨어 (필요에 따라 origins 설정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggerMiddleware)

# API 라우터 포함 (예: 버전 v1)
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info('App started')


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI App"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8090,
                        help="Port number for the server")
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=True)
