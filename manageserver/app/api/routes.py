from fastapi import APIRouter
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
    """ 거래 요청을 저장하고 거래 ID 반환 후 즉시 인증 또는 거래 실행 """
    trade_id = kakao_notifier.save_trade_request(trade.user_id, trade.position, trade.justification)

    # ✅ 거래 요청 저장 후 즉시 `send_trade_request()` 실행
    result = kakao_notifier.send_trade_request(trade_id)

    return {"trade_id": trade_id, "message": result}


from fastapi import APIRouter, Query

@router.get("/callback")
async def kakao_callback(code: str = Query(...), state: str = Query(None)):  # ✅ state로 받기
    """ 카카오 OAuth 인증 후 해당 거래 정보를 조회하여 메시지 전송 """
    if not state:
        return {"error": "거래 ID (state) 누락"}

    trade_id = int(state)  # ✅ state 값을 trade_id로 변환

    trade_data = kakao_notifier.get_trade_request(trade_id)
    if not trade_data:
        return {"error": "거래 요청을 찾을 수 없습니다."}

    user_id, _, _ = trade_data
    access_token = kakao_notifier.get_access_token(user_id, code)

    if access_token:
        result = kakao_notifier.send_trade_request(trade_id)
        return {"message": "카카오 인증 완료 및 거래 메시지 전송", "result": result}
    else:
        return {"error": "카카오 인증 실패"}
