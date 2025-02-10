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

# StartNode 및 EndNode 정의
START = "START"
END = "END"

class StartNode:
    def __init__(self, name: str = START) -> None:
        """
        그래프의 시작점을 나타내는 노드입니다.
        초기 상태를 설정하고 처리 흐름을 시작합니다.

        Attributes:
            name (str): 노드 이름, 기본값은 "START"
        """
        
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
        - 품질 평가
        - 품질 감독
        - 최종 분석
    3. 시작/종료 노드

    Returns:
        Graph: 설정된 분석 워크플로우 그래프

    Note:
        품질 감독 노드(ReportSupervisorAgent)는 조건부 엣지를 통해
        필요한 경우 특정 분석을 재수행하도록 제어합니다.
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
    #deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
    scorer_node = ReportScorerAgent("ReportScorerAgent", eval_model="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct")
    supervisor_node = ReportSupervisorAgent("ReportSupervisorAgent", quality_threshold=5.0)
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
    graph.add_edge("MacroeconomicAnalysisAgent", "FinancialReportsAnalysisAgent")
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

def run_graph_stream(initial_state: GraphState):
    """
    초기 상태를 받아 그래프를 실행하고 실행 과정을 스트리밍합니다.

    Args:
        initial_state (GraphState): 초기 그래프 상태
            필수 키:
            - company_name: 기업명
            - company_code: 종목 코드
            - customer_id: 고객 ID
            - task_id: 작업 ID
            - date: 분석 날짜
            - user_assets: 투자 가능 자산
            - investment_persona: 투자 성향

    Returns:
        list: (노드명, 상태) 튜플의 리스트
            그래프 실행 과정의 각 단계별 상태를 포함
    """
    
    graph = create_graph()
    return list(graph.run_stream(initial_state))

def main():
    """
    투자 분석 워크플로우의 메인 실행 함수입니다.

    다음 단계로 실행됩니다:
    1. 초기 상태 설정 (테스트용 데이터 포함)
    2. 그래프 생성
    3. 스트리밍 방식으로 그래프 실행
    4. 각 노드 실행 결과 로깅
    5. 최종 보고서 및 투자 의견 출력

    Example:
        >>> initial_state = {
        ...     "company_name": "LG화학",
        ...     "company_code": "051910",
        ...     "investment_persona": "중고위험(적극적)",
        ...     "user_assets": 10000000.0
        ... }
        >>> main()  # 전체 분석 프로세스 실행
    """
    
    initial_state: GraphState = {
        "company_name": "LG화학",
        "company_code": "051910",
        "customer_id": "uuid-1234-5678",
        "task_id": "task-001",
        "date": "2025-03-15",
        "user_assets": 10000000.0,
        "financial_query": "2025년 3월 기준, 해당 기업의 재무 리포트 및 투자 전망 분석",
        "investment_persona": "중고위험(적극적)"
    }
    
    final_state = None
    graph = create_graph()
    for node_name, state in graph.run_stream(initial_state):
        print(f"[Stream] {node_name} 완료. 현재 state keys: {list(state.keys())}")
        final_state = state

    print("\n===== 최종 보고서와 매매 의견 및 포트폴리오 =====")
    
    # 최종 보고서는 FinalAnalysisAgent 또는 EndNode에서 생성된 state에 있습니다.
    print(final_state.get("final_report", "최종 보고서가 생성되지 않았습니다."))
    print(final_state.get("integrated_report", "최종 통합보고서가 생성되지 않았습니다."))

if __name__ == "__main__":
    main()
