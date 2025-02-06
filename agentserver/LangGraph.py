# LangGraph.py

from LangGraph_base import Graph, GraphState
from fin_Financial_Statements_agent import EnterpriseReportAgent ## 수정 예정
from fin_news_analysis_agent import NewsAnalysisAgent
from fin_macro_index_agent import MacroeconomicAnalysisAgent  
from fin_reports_analysis_agent import FinancialReportsAnalysisAgent
from fin_report_daily_chart_agent import DailyChartAnalysisAgent
from report_integration_agent import ReportIntegrationNode ## 수정 예정
from final_analysis_agent import FinalAnalysisAgent ## 수정 예정

def main():
    graph = Graph()

    # 에이전트 노드 인스턴스 생성
    enterprise_node = EnterpriseReportAgent("EnterpriseReportAgent")
    news_node = NewsAnalysisAgent("NewsAnalysisAgent")
    macro_node = MacroeconomicAnalysisAgent("MacroeconomicAnalysisAgent")
    financial_node = FinancialReportsAnalysisAgent("FinancialReportsAnalysisAgent")
    daily_chart_node = DailyChartAnalysisAgent("DailyChartAnalysisAgent")
    integration_node = ReportIntegrationNode("ReportIntegrationNode")
    final_node = FinalAnalysisAgent("FinalAnalysisAgent")

    # 노드 추가 
    for node in [enterprise_node, news_node, macro_node, financial_node, daily_chart_node, integration_node, final_node]:
        graph.add_node(node)

    # 엣지 연결 (순차적 흐름 수정 예정)
    graph.add_edge("EnterpriseReportAgent", "NewsAnalysisAgent")
    graph.add_edge("NewsAnalysisAgent", "MacroeconomicAnalysisAgent")
    graph.add_edge("MacroeconomicAnalysisAgent", "FinancialReportsAnalysisAgent")
    graph.add_edge("FinancialReportsAnalysisAgent", "DailyChartAnalysisAgent")
    graph.add_edge("DailyChartAnalysisAgent", "ReportIntegrationNode")
    graph.add_edge("ReportIntegrationNode", "FinalAnalysisAgent")

    # 초기 상태 설정
    initial_state: GraphState = {
        "company_name": "LG화학",
        "user_assets": 10000000.0,
        "financial_query": "2025년 3월 기준, 해당 기업의 재무 리포트 및 투자 전망 분석"
    }

    final_state = None
    for node_name, state in graph.run_stream(initial_state):
        print(f"[Stream] {node_name} 완료. 현재 state keys: {list(state.keys())}")
        final_state = state

    print("\n===== 최종 보고서 =====")
    print(final_state.get("final_report", "최종 보고서가 생성되지 않았습니다."))

if __name__ == "__main__":
    main()