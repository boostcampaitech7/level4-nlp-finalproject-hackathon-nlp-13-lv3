from fastapi import APIRouter
from app.api.v1 import endpoints, user, auth, invest

api_router = APIRouter()

# 예시 엔드포인트(예: /api/v1/example) 포함
api_router.include_router(
    endpoints.router, prefix="/example", tags=["Example"])
api_router.include_router(
    user.router, prefix="/user", tags=["User"])
api_router.include_router(
    auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    invest.router, prefix="/invest", tags=["Invest"])
