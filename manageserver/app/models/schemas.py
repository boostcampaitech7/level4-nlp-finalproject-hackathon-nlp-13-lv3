from pydantic import BaseModel

class TradeRequest(BaseModel):
    """ 거래 요청을 위한 Pydantic 스키마 """
    user_id: str
    stock_code: str
    position: str  # 예: "매수" 또는 "매도"
    justification: str  # 거래 근거 설명
    task_id: str #보고서 번호

class RejectionRequest(BaseModel):
    """ 사용자가 거래를 거부할 때 사용되는 스키마 """
    user_id: str
    investor_type: str  # 예: "저위험 투자자", "고위험 투자자" 등
    company_code: str  # 6자리 기업 코드

class TradeResponse(BaseModel):
    """ 거래 요청 응답 스키마 """
    trade_id: int
    message: str
