"""
FastAPI 서버 진입점 (Entry Point)
- 서버 초기화 및 라우터 등록
- 실행 시 Uvicorn을 이용하여 API 서버를 실행
"""

from fastapi import FastAPI
from app.api.routes import router

# FastAPI 앱 초기화
app = FastAPI(
    title="매매관리 API",
    description="거래 요청 저장, 사용자 인증 및 승인 요청, 실시간 주가 조회, 매매 내역 기록 및 관리 기능을 제공하는 API",
    version="1.0.0"
)

# 라우터 등록
app.include_router(router)

# Uvicorn을 이용한 서버 실행 (개발 환경에서는 reload=True 설정)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"  # 로그 레벨 설정 (debug, info, warning, error)
    )
