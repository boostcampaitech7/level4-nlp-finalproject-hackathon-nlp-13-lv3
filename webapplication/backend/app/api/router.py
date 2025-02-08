from fastapi import APIRouter
from app.api.v1 import endpoints
from app.api.v1 import user
api_router = APIRouter()

# 예시 엔드포인트(예: /api/v1/example) 포함
api_router.include_router(
    endpoints.router, prefix="/example", tags=["Example"])
api_router.include_router(
    user.router, prefix="/user", tags=["User"])
api_router.include_router(
    user.router, prefix="/auth", tags=["Auth"])
