import os

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
import requests

from sqlalchemy.orm import Session

from app.schemas.example import ExampleRequest, ExampleResponse

from app.db.session import get_db
from dotenv import load_dotenv
from starlette.requests import Request as StarletteRequest

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']


@router.get("/google/callback")
async def google_login_callback(request: Request, db: Session = Depends(get_db)):
    logger = request.state.logger

    code = request.query_params.get("code")
    logger.debug(f"code: {code}")
    if not code:
        logger.error("로그인 실패 - code 없음")
        return "로그인 실패"
    # 액세스 토큰 요청
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }
    )

    # 액세스 토큰 처리
    if token_response.status_code == 200:
        logger.info("로그인 성공")
        token_response_json = token_response.json()
        access_token = token_response_json.get("access_token")

        # 사용자 정보 조회
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_info_response.json()

        logger.debug(f"user_info: {user_info}")
        # 로그인 성공 후 처리
        return RedirectResponse(url="http://localhost:8502/?page=dashboard", status_code=302)
    else:
        logger.error("로그인 실패")
        return "로그인 실패"
