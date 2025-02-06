from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.agents.kakao_notification import KakaoNotification

router = APIRouter()
kakao_notifier = KakaoNotification()

class TradeRequest(BaseModel):
    user_id: str
    position: str
    justification: str

@router.post("/trade")
async def execute_trade(trade: TradeRequest):
    """
    매매 요청 처리
    - 카카오 인증이 안 되어 있으면 인증 요청 링크 전송
    """
    result = kakao_notifier.send_message(trade.user_id, f"📢 매매 요청: {trade.position}")
    return {"message": result}

@router.get("/callback")
async def kakao_callback(request: Request):
    """
    카카오 인증 후 콜백 처리
    """
    code = request.query_params.get("code")
    user_id = request.query_params.get("state", "unknown_user")  # 사용자가 누구인지 식별

    access_token, refresh_token = kakao_notifier.get_access_token(code)
    if access_token:
        kakao_notifier.user_tokens[user_id] = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        return {"message": f"✅ {user_id}의 인증이 완료되었습니다!"}
    else:
        return {"error": "❌ 인증 실패"}
