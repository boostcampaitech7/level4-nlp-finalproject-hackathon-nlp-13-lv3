from fastapi import APIRouter, Query, HTTPException
import os
import json
import requests
from app.models.schemas import TradeRequest, TradeResponse, RejectionRequest
from app.services.kakao_notification import KakaoNotification
from app.core.database import Database

router = APIRouter()
db = Database()
kakao_notifier = KakaoNotification()


@router.post("/trade", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest):
    """ 거래 요청을 저장하고 거래 ID 반환 후 즉시 인증 또는 거래 실행 """
    print(f"🔍 [DEBUG] 요청 데이터: {trade}")

    trade_id = db.save_trade_request(trade.user_id, trade.stock_code, trade.position, trade.justification,
                                     trade.task_id)

    result = kakao_notifier.send_trade_request(trade_id)

    # ✅ `result`가 dict이면 JSON 문자열로 변환
    if isinstance(result, dict):
        result = json.dumps(result, ensure_ascii=False)  # 한글도 유지

    return TradeResponse(trade_id=trade_id, message=result)


@router.get("/callback")
async def kakao_callback(code: str = Query(...), state: str = Query(None)):
    """ 카카오 OAuth 인증 후 액세스 토큰을 받아서 저장 """
    if not state:
        return {"error": "거래 ID (state) 누락"}

    trade_id = int(state)

    # ✅ 거래 요청 데이터 조회
    trade_data = db.get_trade_request(trade_id)
    print(f"🔍 [DEBUG] trade_data: {trade_data}")

    if not trade_data:
        return {"error": "거래 요청을 찾을 수 없습니다."}

    # ✅ `trade_data` 변수 할당 (task_id 포함)
    user_id, stock_code, position, justification, task_id = trade_data

    # ✅ 카카오 API에서 액세스 토큰 요청
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

    token_data = response.json()
    access_token = token_data.get("access_token")

    # ✅ DB에 액세스 토큰 저장 (메서드 추가 필요)
    try:
        db.save_tokens(user_id, access_token, "")
        print(f"✅ [INFO] 사용자 {user_id}의 액세스 토큰 저장 완료")
    except AttributeError:
        return {"error": "DB 저장 오류: save_tokens 메서드가 없습니다."}

    return {"message": "카카오 인증 완료 및 액세스 토큰 저장", "access_token": access_token}



@router.post("/reject")
async def reject_trade(request: RejectionRequest):
    """ 사용자가 거래를 거부했을 때 API 요청 처리 """
    # 거부 API로 요청을 전송
    response = kakao_notifier.handle_rejection(request.user_id, request.investor_type, request.company_code)

    if response.status_code == 200:
        return {"message": "거부 요청이 성공적으로 처리되었습니다."}
    else:
        raise HTTPException(status_code=500, detail="거부 요청 처리 중 오류 발생")
