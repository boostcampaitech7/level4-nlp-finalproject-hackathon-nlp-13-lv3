from fastapi import APIRouter
from app.api.v1 import endpoints
from app.api.v1 import user
from app.api.v1 import analysis
from app.api.v1 import invest_task
#from app.api.v1.report import no_stream_invest
#from app.api.v1.report import stream_invest

api_router = APIRouter()

# 예시 엔드포인트(예: /api/v1/example) 포함
api_router.include_router(
    endpoints.router, prefix="/example", tags=["Example"])
api_router.include_router(
    user.router, prefix="/user", tags=["User"])
api_router.include_router(
    analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(
    invest_task.router, prefix="/invest", tags=["InvestTask"])
#api_router.include_router(no_stream_invest, prefix="/no-stream-invest", tags=["NoStreaming"])
#api_router.include_router(stream_invest, prefix="/stream-invest", tags=["Streaming"])