# LangGraph.py

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
        self.name = name
    def process(self, state: GraphState) -> GraphState:
        print(f"[{self.name}] 시작 노드: 초기 state 설정 완료")
        return state

class EndNode:
    def __init__(self, name: str = END) -> None:
        self.name = name
    def process(self, state: GraphState) -> GraphState:
        print(f"[{self.name}] 종료 노드: 최종 state 도달")
        return state

def create_graph() -> Graph:
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
    graph = create_graph()
    return list(graph.run_stream(initial_state))

def main():
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
    # 최종 보고서는 FinalAnalysisAgent 또는 EndNode에서 생성된 state에 있음
    print(final_state.get("final_report", "최종 보고서가 생성되지 않았습니다."))
    print(final_state.get("integrated_report", "최종 통합보고서가 생성되지 않았습니다."))

if __name__ == "__main__":
    main()
