from fastapi import APIRouter
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.graph import run_graph

router = APIRouter()

@router.post("/", response_model=AnalysisResponse)
def get_analysis_report(request: AnalysisRequest):
    """
    요청 데이터를 초기 상태로 하여 LangGraph를 실행하고 최종 분석 보고서를 반환합니다.
    """
    initial_state = request.dict()
    final_state = run_graph(initial_state)
    final_report = final_state.get("final_report", "최종 보고서 생성 실패")
    return AnalysisResponse(final_report=final_report)
