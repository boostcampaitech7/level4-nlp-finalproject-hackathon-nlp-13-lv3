from fastapi import APIRouter, Query, HTTPException
import os
import json
import requests
from app.models.schemas import TradeRequest, TradeResponse, RejectionRequest
from app.services.kakao_notification import KakaoNotification
from app.core.database import Database

# FastAPI 라우터 객체 생성
router = APIRouter()

# 데이터베이스 및 카카오 알림 서비스 인스턴스 초기화
db = Database()
kakao_notifier = KakaoNotification()


@router.post("/trade", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest):
    """
    거래 요청을 저장하고, 거래 ID를 반환 후 즉시 카카오톡을 통해 승인 요청을 보냄.

    Parameters:
        trade (TradeRequest): 거래 요청 객체 (user_id, stock_code, position, justification 포함)

    Returns:
        TradeResponse: 거래 ID와 처리 결과 메시지
    """

    # 거래 요청을 데이터베이스에 저장
    trade_id = db.save_trade_request(
        trade.user_id, trade.stock_code, trade.position, trade.justification, trade.task_id
    )

    # 거래 요청 후 카카오톡 메시지 전송
    result = kakao_notifier.send_trade_request(trade_id)

    # 결과가 dict 형태일 경우 JSON 문자열로 변환
    if isinstance(result, dict):
        result = json.dumps(result, ensure_ascii=False)  # 한글 유지

    return TradeResponse(trade_id=trade_id, message=result)


@router.get("/callback")
async def kakao_callback(code: str = Query(...), state: str = Query(None)):
    """
    카카오 OAuth 인증 후 액세스 토큰을 받아서 저장.

    Parameters:
        code (str): 카카오 OAuth 인증 코드
        state (str, optional): 거래 ID (state 값으로 전달됨)

    Returns:
        dict: 인증 결과 메시지 및 액세스 토큰
    """
    if not state:
        return {"error": "거래 ID (state) 누락"}

    trade_id = int(state)

    # 거래 요청 데이터 조회
    trade_data = db.get_trade_request(trade_id)

    if not trade_data:
        return {"error": "거래 요청을 찾을 수 없습니다."}

    # `trade_data` 변수 할당 (task_id 포함)
    user_id, stock_code, position, justification, task_id = trade_data

    # 카카오 API에서 액세스 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": os.getenv("KAKAO_CLIENT_ID"),
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
        "code": code
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        return {"error": "카카오 인증 실패", "response": response.json()}

    # 액세스 토큰 파싱
    token_data = response.json()
    access_token = token_data.get("access_token")

    # DB에 액세스 토큰 저장
    try:
        db.save_tokens(user_id, access_token, "")
    except AttributeError:
        return {"error": "DB 저장 오류: save_tokens 메서드가 없습니다."}

    return {"message": "카카오 인증 완료 및 액세스 토큰 저장", "access_token": access_token}


@router.post("/reject")
async def reject_trade(request: RejectionRequest):
    """
    사용자가 거래를 거부했을 때 API 요청 처리.

    Parameters:
        request (RejectionRequest): 거부 요청 정보 (user_id, investor_type, company_code 포함)

    Returns:
        dict: 거부 요청 처리 결과 메시지
    """
    # 거부 API로 요청 전송
    response = kakao_notifier.handle_rejection(request.user_id, request.investor_type, request.company_code)

    if response.status_code == 200:
        return {"message": "거부 요청이 성공적으로 처리되었습니다."}
    else:
        raise HTTPException(status_code=500, detail="거부 요청 처리 중 오류 발생")
