from app.langgraph_base import Graph, GraphState
from app.fin_financial_statements_agent import FinancialStatementsAnalysisAgent
from app.fin_news_analysis_agent import NewsAnalysisAgent
from app.fin_macro_index_agent import MacroeconomicAnalysisAgent
from app.fin_reports_analysis_agent import FinancialReportsAnalysisAgent
from app.fin_report_daily_chart_agent import DailyChartAnalysisAgent
from app.report_integration_agent import ReportIntegrationNode  # 수정 예정
from app.final_analysis_agent import FinalAnalysisAgent  # 수정 예정
from typing import List, Tuple

def run_graph(initial_state: GraphState) -> List[Tuple[str, GraphState]]:
    """
    langgraph_base.py의 Graph를 생성, 각 노드(에이전트)를 추가하고,
    edges를 연결한 후 run_stream(initial_state) 결과를 모두 수집하여 반환.
    """
    graph = Graph()

    nodes = [
        FinancialStatementsAnalysisAgent("FinancialStatementsAnalysisAgent"),
        NewsAnalysisAgent("NewsAnalysisAgent"),
        MacroeconomicAnalysisAgent("MacroeconomicAnalysisAgent"),
        FinancialReportsAnalysisAgent("FinancialReportsAnalysisAgent"),
        DailyChartAnalysisAgent("DailyChartAnalysisAgent"),
        ReportIntegrationNode("ReportIntegrationNode"),
        FinalAnalysisAgent("FinalAnalysisAgent"),
    ]

    for node in nodes:
        graph.add_node(node)

    # 순차 실행
    graph.add_edge("FinancialStatementsAnalysisAgent", "NewsAnalysisAgent")
    graph.add_edge("NewsAnalysisAgent", "MacroeconomicAnalysisAgent")
    graph.add_edge("MacroeconomicAnalysisAgent", "FinancialReportsAnalysisAgent")
    graph.add_edge("FinancialReportsAnalysisAgent", "DailyChartAnalysisAgent")
    graph.add_edge("DailyChartAnalysisAgent", "ReportIntegrationNode")
    graph.add_edge("ReportIntegrationNode", "FinalAnalysisAgent")

    intermediate_steps: List[Tuple[str, GraphState]] = []
    for node_name, state in graph.run_stream(initial_state):
        # 여기에서 node_name, state를 통해 중간 정보를 확인하거나 DB 업데이트 가능
        print(f"Node {node_name} completed.")
        msg = state.get(f"{node_name}_status_message", "N/A")
        st = state.get(f"{node_name}_status", "N/A")
        print(f"Status Message: {msg}")
        print(f"Status: {st}\n")

        # 상태를 copy()해서 저장 (이후 용도)
        intermediate_steps.append((node_name, state.copy()))

    return intermediate_steps
