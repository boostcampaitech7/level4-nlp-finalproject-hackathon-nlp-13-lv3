import streamlit as st
import time
from typing import Annotated, List, Iterator, Tuple
from typing_extensions import TypedDict

# =============================================================================
# 상태(state) 정의: 각 노드가 공유하는 데이터 구조를 명시적으로 선언 (Optional 키들은 total=False 사용)
# =============================================================================
class GraphState(TypedDict, total=False):
    company_name: Annotated[str, "The company for which the report is generated"]
    market_data: Annotated[dict, "Market data from market API"]
    news: Annotated[str, "News sentiment text"]
    financial_data: Annotated[dict, "Financial data (e.g., EPS, P/E)"]
    order_book: Annotated[dict, "Order book information"]
    macroeconomic: Annotated[dict, "Macroeconomic information"]
    financial_query: Annotated[str, "Query string for financial analysis"]
    fundamental_score: Annotated[float, "Calculated fundamental score"]
    technical_score: Annotated[float, "Calculated technical score"]
    sentiment_score: Annotated[int, "Calculated sentiment score"]
    liquidity_indicator: Annotated[float, "Calculated liquidity indicator"]
    macro_score: Annotated[float, "Calculated macroeconomic score"]
    financial_report_analysis: Annotated[str, "Result from financial reports analysis agent"]
    decision_score: Annotated[float, "Aggregate decision score"]
    final_decision: Annotated[str, "Final investment decision (Buy, Sell, Hold)"]
    rollback: Annotated[str, "If set, indicates a node to rollback to"]
    risk_adjusted_decision: Annotated[str, "Risk-adjusted decision"]
    execution_result: Annotated[str, "Result of trade execution"]
    feedback: Annotated[str, "Feedback after execution"]
    web_search_info: Annotated[str, "Additional info from web search"]
    final_report: Annotated[str, "The final generated investment report"]

# =============================================================================
# 외부 모듈 임포트: financial_reports_analysis_agent.py에 정의된 클래스

# =============================================================================
import sys
import os

# 현재 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# 부모 디렉토리 (financial_reports_analysis_agent.py가 있는 경로) 추가
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

# sys.path에 부모 디렉토리 추가
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from financial_reports_analysis_agent import FinancialReportsAnalysisAgent


# =============================================================================
# 기본 Node 클래스
# =============================================================================
class Node:
    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, state: GraphState) -> GraphState:
        """
        각 노드는 process() 메서드를 오버라이딩하여 자신의 기능을 수행합니다.
        입력 state를 수정한 후 반환합니다.
        """
        print(f"[{self.name}] 기본 process() 호출")
        return state

# =============================================================================
# 개별 에이전트(노드) 구현 (GraphState 타입을 사용)
# =============================================================================

class DataIngestionNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("DataIngestionNode: 외부 소스에서 데이터 수집 중...")
        # 모의 데이터 할당
        state['market_data'] = {"price": 100, "volume": 1000}
        state['news'] = "Positive market sentiment"
        state['financial_data'] = {"EPS": 2.5, "P/E": 15}
        state['order_book'] = {"bid": 99.5, "ask": 100.5}
        state['macroeconomic'] = {"GDP_growth": 2.5, "interest_rate": 1.5}
        # 재무 분석 노드에서 사용할 쿼리 전달
        state["financial_query"] = "2025년 3월 기준 주요 기업의 재무 보고서를 분석해줘."
        time.sleep(0.5)  # 데이터 수집 지연 시뮬레이션
        return state

class FundamentalAnalysisNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("FundamentalAnalysisNode: 재무 데이터를 분석 중...")
        fd = state.get('financial_data', {})
        eps = fd.get("EPS", 0)
        pe = fd.get("P/E", 0)
        fundamental_score = eps / pe if pe != 0 else 0
        state['fundamental_score'] = fundamental_score
        time.sleep(0.2)
        return state

class TechnicalAnalysisNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("TechnicalAnalysisNode: 기술적 분석 수행 중...")
        md = state.get('market_data', {})
        price = md.get("price", 0)
        technical_score = price * 0.1  # 임의 계산
        state['technical_score'] = technical_score
        time.sleep(0.2)
        return state

class NewsSentimentNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("NewsSentimentNode: 뉴스 감성 분석 중...")
        news = state.get('news', "")
        if "Positive" in news:
            sentiment_score = 1
        elif "Negative" in news:
            sentiment_score = -1
        else:
            sentiment_score = 0
        state['sentiment_score'] = sentiment_score
        time.sleep(0.2)
        return state

class OrderBookAnalysisNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("OrderBookAnalysisNode: 호가창 데이터 분석 중...")
        ob = state.get('order_book', {})
        bid = ob.get("bid", 0)
        ask = ob.get("ask", 0)
        if bid and ask:
            liquidity_indicator = (ask - bid) / ((ask + bid) / 2)
        else:
            liquidity_indicator = 0
        state['liquidity_indicator'] = liquidity_indicator
        time.sleep(0.2)
        return state

class MacroeconomicAnalysisNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("MacroeconomicAnalysisNode: 거시경제 지표 평가 중...")
        me = state.get('macroeconomic', {})
        gdp_growth = me.get("GDP_growth", 0)
        interest_rate = me.get("interest_rate", 0)
        macro_score = gdp_growth - interest_rate
        state['macro_score'] = macro_score
        time.sleep(0.2)
        return state

class FinancialReportsAnalysisNode(Node):
    """
    외부 모듈 (financial_reports_analysis_agent.py)의 FinancialReportsAnalysisAgent를
    래핑하여 재무 보고서 분석을 수행하는 노드입니다.
    """
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.agent = FinancialReportsAnalysisAgent()

    def process(self, state: GraphState) -> GraphState:
        st.write("FinancialReportsAnalysisNode: 재무 보고서 분석 수행 중...")
        query = state.get("financial_query", "기본 재무 분석 query")
        analysis_result = self.agent.run(query)
        state["financial_report_analysis"] = analysis_result
        time.sleep(0.2)
        return state

class AggregationDecisionNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("AggregationDecisionNode: 분석 결과 종합 및 투자 의사 결정 중...")
        fundamental = state.get('fundamental_score', 0)
        technical = state.get('technical_score', 0)
        sentiment = state.get('sentiment_score', 0)
        liquidity = state.get('liquidity_indicator', 0)
        macro = state.get('macro_score', 0)
        # 재무보고서 분석 결과가 있을 경우 추가 가중치 부여 (예: "목표 주가" 포함 여부)
        financial_analysis = state.get("financial_report_analysis", "")
        financial_bonus = 1 if "목표 주가" in financial_analysis else 0

        decision_score = (fundamental * 0.3 +
                          technical * 0.3 +
                          sentiment * 0.2 +
                          (-liquidity) * 0.1 +
                          macro * 0.1 +
                          financial_bonus * 0.5)
        state['decision_score'] = decision_score

        if decision_score > 10:
            decision = "Buy"
        elif decision_score < 5:
            decision = "Sell"
        else:
            decision = "Hold"
        state['final_decision'] = decision

        st.write(f"  종합 점수: {decision_score:.2f}, 최종 결정: {decision}")
        time.sleep(0.2)
        return state

class EvaluationNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("EvaluationNode: 중간 평가 수행 중...")
        decision = state.get('final_decision', None)
        if decision == "Hold":
            st.write("  평가 결과: 결정이 'Hold' 상태입니다. 추가 정보를 위해 WebSearchNode로 롤백합니다.")
            state["rollback"] = "WebSearch"
        else:
            st.write("  평가 결과: 결정이 만족스럽습니다. 다음 단계로 진행합니다.")
        time.sleep(0.2)
        return state

class WebSearchNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("WebSearchNode: 웹 검색 수행 중...")
        additional_info = "Additional market insights obtained from web search."
        state['web_search_info'] = additional_info
        st.write("  웹 검색 결과:", additional_info)
        time.sleep(0.2)
        return state

class RiskManagementNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("RiskManagementNode: 리스크 평가 및 결정 조정 중...")
        decision = state.get('final_decision', 'Hold')
        md = state.get('market_data', {})
        volume = md.get("volume", 0)
        if volume < 500:
            st.write("  위험 평가: 거래량이 낮아 위험도가 높음 -> Hold로 조정")
            risk_adjusted_decision = "Hold"
        else:
            risk_adjusted_decision = decision
        state['risk_adjusted_decision'] = risk_adjusted_decision
        time.sleep(0.2)
        return state

class TradeExecutionNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("TradeExecutionNode: 매매 주문 실행 중...")
        decision = state.get('risk_adjusted_decision', 'Hold')
        if decision == "Buy":
            execution_result = "Executed BUY order."
        elif decision == "Sell":
            execution_result = "Executed SELL order."
        else:
            execution_result = "No trade executed (Hold)."
        state['execution_result'] = execution_result
        st.write(f"  매매 결과: {execution_result}")
        time.sleep(0.2)
        return state

class FeedbackNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("FeedbackNode: 거래 및 시장 피드백 수집 중...")
        execution_result = state.get('execution_result', 'No result')
        st.write(f"  피드백: {execution_result}")
        state['feedback'] = "Feedback logged"
        time.sleep(0.2)
        return state

# =============================================================================
# 새로 추가: ReportGenerationNode
# 최종적으로 모든 에이전트의 결과를 종합하여 투자 보고서를 생성합니다.
# =============================================================================
class ReportGenerationNode(Node):
    def process(self, state: GraphState) -> GraphState:
        st.write("ReportGenerationNode: 최종 보고서 생성 중...")
        company = state.get("company_name", "N/A")
        decision = state.get("final_decision", "N/A")
        decision_score = state.get("decision_score", 0)
        financial_analysis = state.get("financial_report_analysis", "N/A")
        risk_adjusted = state.get("risk_adjusted_decision", "N/A")
        execution_result = state.get("execution_result", "N/A")
        feedback = state.get("feedback", "N/A")
        
        report = (
            f"【{company} 투자 보고서】\n"
            f"---------------------------------\n"
            f"최종 투자 의견: {decision} (점수: {decision_score:.2f})\n"
            f"재무 보고서 분석 결과: {financial_analysis}\n"
            f"리스크 조정 후 결정: {risk_adjusted}\n"
            f"실제 매매 실행 결과: {execution_result}\n"
            f"피드백: {feedback}\n"
            f"---------------------------------\n"
            "추가 분석 및 개선 사항은 별도 참고 바랍니다.\n"
        )
        state["final_report"] = report
        st.write("최종 보고서 생성 완료.")
        time.sleep(0.2)
        return state

# =============================================================================
# Graph 클래스: 노드와 엣지를 관리하며 전체 워크플로우를 실행 (멀티턴/롤백/스트리밍 지원)
# =============================================================================
class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, List[str]] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node
        if node.name not in self.edges:
            self.edges[node.name] = []

    def add_edge(self, source: str, destination: str) -> None:
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Source 또는 Destination 노드가 그래프에 존재하지 않습니다.")
        self.edges[source].append(destination)

    def get_topological_order(self) -> List[str]:
        in_degree: dict[str, int] = {node: 0 for node in self.nodes}
        for src, dest_list in self.edges.items():
            for dest in dest_list:
                in_degree[dest] += 1
        queue = [node for node, deg in in_degree.items() if deg == 0]
        topo_order: List[str] = []
        while queue:
            current = queue.pop(0)
            topo_order.append(current)
            for neighbor in self.edges.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(topo_order) != len(self.nodes):
            raise ValueError("그래프에 사이클이 존재합니다. 위상 정렬 실패.")
        return topo_order

    def run_stream(self, initial_state: GraphState) -> Iterator[Tuple[str, GraphState]]:
        """
        위상 정렬 순서에 따라 각 노드를 순차적으로 실행합니다.
        중간에 rollback 요청이 있을 경우 해당 노드로 돌아가는 멀티턴 실행을 지원하며,
        각 노드 실행 후 (노드 이름, state)를 yield하여 스트리밍 방식으로 중간 결과를 확인할 수 있습니다.
        """
        topo_order = self.get_topological_order()
        current_index = 0
        state: GraphState = initial_state

        st.write("\n===== Graph Execution (Streaming) 시작 =====\n")
        st.write("초기 위상 정렬 순서:")
        st.write(" -> ".join(topo_order))
        st.write("\n-------------------------------\n")

        while current_index < len(topo_order):
            node_name = topo_order[current_index]
            node = self.nodes[node_name]
            st.write(f"==> 노드 실행: {node_name}")
            state = node.process(state)
            
            # 중간 결과 스트리밍
            yield node_name, state
            
            # 롤백 요청이 있으면 해당 노드로 돌아감
            if "rollback" in state:
                rollback_target = state["rollback"]
                st.write(f"  [ROLLBACK] {rollback_target} 노드로 돌아갑니다.\n")
                if rollback_target in topo_order:
                    current_index = topo_order.index(rollback_target)
                    del state["rollback"]  # 롤백 요청 삭제
                    continue
                else:
                    st.write("  [ERROR] 롤백 대상 노드가 존재하지 않습니다. 실행 계속...")
            current_index += 1

        st.write("\n===== Graph Execution 종료 =====\n")
        return state

# =============================================================================
# Streamlit 프로토타입 인터페이스
# =============================================================================
st.title("주식 투자 보고서 생성 서비스")
st.markdown("입력된 기업에 대해 여러 에이전트가 분석을 진행한 후 최종 투자 보고서를 생성합니다.")

if st.button("Generate Report"):
    # 초기 상태: 기업명을 LG화학으로 설정 (여기서 초기 설정 변경)
    initial_state: GraphState = {
        "company_name": "LG화학"
    }
    
    # 그래프 인스턴스 생성 및 노드/엣지 구성
    graph = Graph()

    # 각 에이전트(노드) 객체 생성
    data_ingestion = DataIngestionNode("DataIngestion")
    fundamental_analysis = FundamentalAnalysisNode("FundamentalAnalysis")
    technical_analysis = TechnicalAnalysisNode("TechnicalAnalysis")
    news_sentiment = NewsSentimentNode("NewsSentiment")
    order_book_analysis = OrderBookAnalysisNode("OrderBookAnalysis")
    macroeconomic_analysis = MacroeconomicAnalysisNode("MacroeconomicAnalysis")
    financial_reports_analysis = FinancialReportsAnalysisNode("FinancialReportsAnalysis")
    aggregation_decision = AggregationDecisionNode("AggregationDecision")
    evaluation = EvaluationNode("EvaluationNode")
    web_search = WebSearchNode("WebSearch")
    risk_management = RiskManagementNode("RiskManagement")
    trade_execution = TradeExecutionNode("TradeExecution")
    feedback = FeedbackNode("Feedback")
    report_generation = ReportGenerationNode("ReportGeneration")

    # 그래프에 노드 추가
    for node in [data_ingestion, fundamental_analysis, technical_analysis, news_sentiment,
                 order_book_analysis, macroeconomic_analysis, financial_reports_analysis,
                 aggregation_decision, evaluation, web_search, risk_management, trade_execution,
                 feedback, report_generation]:
        graph.add_node(node)

    # 노드 간 엣지(연결) 정의
    graph.add_edge("DataIngestion", "FundamentalAnalysis")
    graph.add_edge("DataIngestion", "TechnicalAnalysis")
    graph.add_edge("DataIngestion", "NewsSentiment")
    graph.add_edge("DataIngestion", "OrderBookAnalysis")
    graph.add_edge("DataIngestion", "MacroeconomicAnalysis")
    graph.add_edge("DataIngestion", "FinancialReportsAnalysis")

    graph.add_edge("FundamentalAnalysis", "AggregationDecision")
    graph.add_edge("TechnicalAnalysis", "AggregationDecision")
    graph.add_edge("NewsSentiment", "AggregationDecision")
    graph.add_edge("OrderBookAnalysis", "AggregationDecision")
    graph.add_edge("MacroeconomicAnalysis", "AggregationDecision")
    graph.add_edge("FinancialReportsAnalysis", "AggregationDecision")

    graph.add_edge("AggregationDecision", "EvaluationNode")
    graph.add_edge("EvaluationNode", "WebSearch")
    graph.add_edge("WebSearch", "RiskManagement")
    # EvaluationNode가 직접 RiskManagement로 진행하는 엣지도 추가 (롤백 없이 진행 시)
    graph.add_edge("EvaluationNode", "RiskManagement")

    graph.add_edge("RiskManagement", "TradeExecution")
    graph.add_edge("TradeExecution", "Feedback")
    # Feedback 후에 최종 보고서 생성
    graph.add_edge("Feedback", "ReportGeneration")

    # 그래프 실행: run_stream()은 제너레이터로 각 중간 state를 스트리밍 출력
    final_state = None
    for node_name, state in graph.run_stream(initial_state):
        st.write(f"*** {node_name} 실행 후 state:")
        st.json(state)
        final_state = state  # 마지막 상태 저장

    st.write("### 최종 상태:")
    st.json(final_state)
    # 최종 보고서 출력
    if final_state and "final_report" in final_state:
        st.write("### 최종 투자 보고서")
        st.text(final_state["final_report"])

