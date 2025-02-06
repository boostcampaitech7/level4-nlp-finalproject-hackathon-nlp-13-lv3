from langgraph.graph import StateGraph
from pydantic import BaseModel

from app.agents.trade_validation_agent import TradeValidationAgent

class TradeState(BaseModel):
    user_id: str                # ✅ 사용자 ID 추가
    position: str
    justification: str
    validation_result: str = "검증 중"
    execution_status: str = "대기 중"

def validate_trade(state: TradeState) -> TradeState:
    """
    매매 검증 수행
    """
    validator = TradeValidationAgent()
    state.validation_result = validator.validate(state.position, state.justification)
    return state

def create_trade_workflow():
    """
    LangGraph 워크플로우 생성
    """
    graph = StateGraph(TradeState)
    graph.add_node("validate_trade", validate_trade)
    graph.set_entry_point("validate_trade")
    return graph.compile()
