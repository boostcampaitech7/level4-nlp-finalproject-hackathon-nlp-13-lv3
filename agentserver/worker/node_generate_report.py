import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import json
from dotenv import load_dotenv
from LangGraph_base import Graph, GraphState
# 에이전트 모듈들
from fin_financial_statements_agent import FinancialStatementsAnalysisAgent
from fin_news_analysis_agent import NewsAnalysisAgent
from fin_macro_index_agent import MacroeconomicAnalysisAgent
from fin_reports_analysis_agent import FinancialReportsAnalysisAgent
from fin_report_daily_chart_agent import DailyChartAnalysisAgent
from report_integration_agent import ReportIntegrationNode
from final_analysis_agent import FinalAnalysisAgent
from fin_report_scorer_agent import ReportScorerAgent
from report_supervisor_agent import ReportSupervisorAgent, get_next_node
from app.db.session import get_db, get_db_session
from app.schemas.db import Stock, Task


MANAGER_API_URL = os.environ.get("MANAGER_API_URL")
load_dotenv()

# StartNode 및 EndNode 정의
START = "START"
END = "END"


class StartNode:
    """
    그래프의 시작점을 나타내는 노드입니다.
    초기 상태를 설정하고 처리 흐름을 시작합니다.

    Attributes:
        name (str): 노드 이름, 기본값은 "START"
    """
    
    def __init__(self, name: str = START) -> None:
        self.name = name

    def process(self, state: GraphState) -> GraphState:
        """
        초기 상태를 확인하고 로깅합니다.

        Args:
            state (GraphState): 초기 그래프 상태

        Returns:
            GraphState: 처리된 초기 상태
        """
        
        print(f"[{self.name}] 시작 노드: 초기 state 설정 완료")
        return state


class EndNode:
    """
    그래프의 종료점을 나타내는 노드입니다.
    모든 처리가 완료된 후의 최종 상태를 처리합니다.

    Attributes:
        name (str): 노드 이름, 기본값은 "END"
    """
    
    def __init__(self, name: str = END) -> None:
        self.name = name

    def process(self, state: GraphState) -> GraphState:
        """
        최종 상태를 확인하고 로깅합니다.

        Args:
            state (GraphState): 최종 그래프 상태

        Returns:
            GraphState: 최종 처리된 상태
        """
        
        print(f"[{self.name}] 종료 노드: 최종 state 도달")
        return state


def create_graph() -> Graph:
    """
    투자 분석을 위한 전체 워크플로우 그래프를 생성합니다.

    그래프는 다음 컴포넌트들로 구성됩니다:
    1. 기본 분석 노드들
        - 재무제표 분석
        - 뉴스 분석
        - 거시경제 분석
        - 증권사 리포트 분석
        - 일봉/차트 분석
    2. 통합 및 평가 노드들
        - 리포트 통합
        - 품질 평가 (EXAONE 모델 사용)
        - 품질 감독 (임계값 5.0)
        - 최종 분석

    Returns:
        Graph: 설정된 분석 워크플로우 그래프
    """
    
    graph = Graph()

    # 에이전트 노드 생성
    start_node = StartNode()
    fs_node = FinancialStatementsAnalysisAgent("FinancialStatementsAnalysisAgent")
    news_node = NewsAnalysisAgent("NewsAnalysisAgent")
    macro_node = MacroeconomicAnalysisAgent("MacroeconomicAnalysisAgent")
    financial_node = FinancialReportsAnalysisAgent("FinancialReportsAnalysisAgent")
    daily_chart_node = DailyChartAnalysisAgent("DailyChartAnalysisAgent")
    integration_node = ReportIntegrationNode("ReportIntegrationNode")
    
    # LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct
    # deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
    scorer_node = ReportScorerAgent(
        "ReportScorerAgent", eval_model="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct")
    supervisor_node = ReportSupervisorAgent(
        "ReportSupervisorAgent", quality_threshold=5.0)
    final_node = FinalAnalysisAgent("FinalAnalysisAgent")
    end_node = EndNode()

    # 노드 추가
    for node in [start_node, fs_node, news_node, macro_node, financial_node, daily_chart_node,
                 integration_node, scorer_node, supervisor_node, final_node, end_node]:
        graph.add_node(node)

    # 엣지 연결 (순차적 흐름)
    graph.add_edge(START, "FinancialStatementsAnalysisAgent")
    graph.add_edge("FinancialStatementsAnalysisAgent", "NewsAnalysisAgent")
    graph.add_edge("NewsAnalysisAgent", "MacroeconomicAnalysisAgent")
    graph.add_edge("MacroeconomicAnalysisAgent",
                   "FinancialReportsAnalysisAgent")
    graph.add_edge("FinancialReportsAnalysisAgent", "DailyChartAnalysisAgent")
    graph.add_edge("DailyChartAnalysisAgent", "ReportIntegrationNode")
    graph.add_edge("ReportIntegrationNode", "ReportScorerAgent")
    graph.add_edge("ReportScorerAgent", "ReportSupervisorAgent")
    graph.add_edge("ReportSupervisorAgent", "FinalAnalysisAgent")
    graph.add_edge("FinalAnalysisAgent", END)

    # 조건부 엣지 설정: Supervisor 노드의 state["next"] 결정에 따라 다음 노드를 선택
    graph.add_conditional_edges("ReportSupervisorAgent", get_next_node, {
        "FinancialStatementsAnalysisAgent": "FinancialStatementsAnalysisAgent",
        "NewsAnalysisAgent": "NewsAnalysisAgent",
        "MacroeconomicAnalysisAgent": "MacroeconomicAnalysisAgent",
        "FinancialReportsAnalysisAgent": "FinancialReportsAnalysisAgent",
        "DailyChartAnalysisAgent": "DailyChartAnalysisAgent",
        "FinalAnalysisAgent": "FinalAnalysisAgent",
        "FINISH": "FinalAnalysisAgent"
    })
    
    return graph


def parse_stock_position(report: str) -> str:
    """
    최종 매매의견에서 주식 포지션을 추출합니다.

    Args:
        report (str): 최종 리포트 문자열
            예: "최종 매매의견: 매도, 자산 배분 제안: 100%"

    Returns:
        str: 추출된 포지션 ("매도", "매수", "관망" 중 하나)
            보고서에서 매매의견을 찾지 못할 경우 "관망" 반환

    Example:
        >>> parse_stock_position("최종 매매의견: 매수, 자산 배분 제안: 30%")
        "매수"
    """
    
    if "매도" in report:
        return "매도"
    elif "매수" in report:
        return "매수"
    elif "관망" in report:
        return "관망"
    else:
        return "관망"


def main():
    """
    투자 분석 워크플로우의 메인 실행 함수입니다.

    다음 단계로 실행됩니다:
    1. DB에서 '시작 전' 상태의 Task 조회
    2. 초기 상태 설정 및 Task 상태 업데이트
    3. 그래프 생성 및 실행
    4. 분석 결과 처리 및 DB 업데이트
        - 매매 포지션 추출
        - 리포트 저장
        - 상태 업데이트

    Database Updates:
        - Task 상태 변경: "시작 전" -> "생성 중" -> "완료"/"실패"
        - 생성된 리포트 저장
        - 매매 포지션 및 근거 업데이트
        - 수정 시간 업데이트

    Error Handling:
        - 예외 발생 시 Task 상태를 "실패"로 변경
        - 에러 메시지를 status_message에 저장
        - DB 트랜잭션 롤백

    Note:
        환경 변수 MANAGER_API_URL이 필요합니다.
    """
    
    with get_db_session() as db:
        try:

            tasks = db.query(Task).filter(Task.status == '시작 전').first()

            if tasks is None:
                print("**************Task가 없습니다.************************")
                return

            initial_state: GraphState = {
                "company_name": tasks.stock_name,
                "company_code": tasks.stock_code,
                "customer_id": tasks.create_user_id,
                "task_id": tasks.task_id,
                "date": tasks.created_at,
                "user_assets": 10000000.0,
                "financial_query": "2025년 3월 기준, 해당 기업의 재무 리포트 및 투자 전망 분석",
                "investment_persona": tasks.investor_type
            }

            db.query(Task).filter(Task.task_id == tasks.task_id).update(
                {Task.status: "생성 중", Task.status_message: "AI 전문가와 분석가가 보고서 생성 중"})
            db.commit()

            final_state = None
            # final_state = {
            #     "final_report" : "최종 보고서가 들어갔다고 가정, 매수",
            #     "integrated_report" : "통합 보고서가 들어갔다고 가정"
            # }
            graph = create_graph()
            for node_name, state in graph.run_stream(initial_state):
                print(
                    f"[Stream] {node_name} 완료. 현재 state keys: {list(state.keys())}")
                final_state = state

            print("\n===== 최종 보고서와 매매 의견 및 포트폴리오 =====")
            
            # 최종 보고서는 FinalAnalysisAgent 또는 EndNode에서 생성된 state에 있습니다.
            print(final_state.get("final_report", "최종 보고서가 생성되지 않았습니다."))
            print(final_state.get("integrated_report", "최종 통합보고서가 생성되지 않았습니다."))

            now = datetime.now(ZoneInfo("Asia/Seoul"))

            if final_state.get("final_report") is not None and final_state.get("integrated_report") is not None:
                stock_position = parse_stock_position(
                    final_state.get("final_report"))

                integrated_report = final_state.get("integrated_report") or ""
                final_report = final_state.get("final_report") or ""
                total_report = final_report + " " + integrated_report

                # db.query(Task).filter(Task.task_id == tasks.task_id).update({Task.status: "완료"})
                db.query(Task).filter(Task.task_id == tasks.task_id).update({Task.status: "완료", Task.report_generate: total_report,
                                                                             Task.stock_position: stock_position, Task.stock_justification: integrated_report, Task.modified_at: now})
                db.commit()
            else:
                raise Exception("최종 보고서 생성 실패")

            # request_data = {
            #     "user_id": tasks.create_user_id,
            #     "stock_code": tasks.stock_code,
            #     "investor_type": tasks.investor_type,
            #     "task_id": tasks.task_id,
            #     "position": stock_position,
            #     "justification": total_report,

            # }
            # response = requests.post(
            #     f"{MANAGER_API_URL}/trade", data=request_data)

            # print(response.text)

        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
            db.query(Task).filter(Task.task_id == tasks.task_id).update(
                {Task.status: "실패", Task.status_message: str(e)})
            db.commit()
            return


if __name__ == "__main__":
    main()
