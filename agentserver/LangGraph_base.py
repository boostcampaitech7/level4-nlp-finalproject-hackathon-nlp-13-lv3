# LangGraph_base.py

from typing import Annotated, List, Tuple, Iterator
from typing_extensions import TypedDict

# GraphState: 모든 노드가 공유하는 상태를 정의합니다.
# (추가 필드: company_code, customer_id, task_id, date)
class GraphState(TypedDict, total=False):
    company_name: Annotated[str, "분석 대상 기업명"]
    company_code: Annotated[str, "기업 코드 (6자리)"]
    customer_id: Annotated[str, "고객 ID (uuid)"]
    task_id: Annotated[str, "작업 ID (DB 기록용)"]
    date: Annotated[str, "날짜"]
    user_assets: Annotated[float, "사용자 보유 자산"]

    # 투자 성향 페르소나
    investment_persona: Annotated[str, "사용자의 투자 성향 (저위험/중위험/중고위험/고위험)"]

    # 각 에이전트별 보고서
    financial_report: Annotated[str, "기업 분석 보고서"]
    news_report: Annotated[str, "뉴스 분석 보고서"]
    macro_report: Annotated[str, "거시경제 분석 보고서"]
    fin_statements_report: Annotated[str, "재무제표 분석 보고서"]
    daily_chart_report: Annotated[str, "일월봉 분석 보고서"]

    # 통합 보고서
    integrated_report: Annotated[str, "통합 보고서"]

    # 최종 분석 결과
    final_opinion: Annotated[str, "최종 매매의견"]
    portfolio_suggestion: Annotated[str, "자산 배분 제안"]

    # 최종 산출물
    final_report: Annotated[str, "최종 보고서"]

    # 보고서 품질 점수
    report_score: Annotated[float, "최종 보고서 점수"]

    # 감독자 노드가 결정한 다음 실행 노드를 지정 (조건부 엣지용)
    next: Annotated[str, "다음 실행할 노드"]


# Node: 각 에이전트(노드)의 기본 클래스
class Node:
    def __init__(self, name: str):
        self.name = name

    def process(self, state: GraphState) -> GraphState:
        print(f"[{self.name}] 기본 process() 호출")
        return state


# Graph: 노드들을 연결하여 실행하는 간단한 DAG 구현
class Graph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, List[str]] = {}
        # 조건부 엣지를 위한 딕셔너리: supervisor 노드 이름 -> (selector 함수, mapping dict)
        self.conditional_edges: dict[str, Tuple[callable, dict[str, str]]] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node
        if node.name not in self.edges:
            self.edges[node.name] = []

    def add_edge(self, source: str, destination: str) -> None:
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Source 또는 Destination 노드가 그래프에 존재하지 않습니다.")
        self.edges[source].append(destination)

    def add_conditional_edges(self, supervisor_node: str, selector: callable, mapping: dict[str, str]) -> None:
        """
        supervisor_node: 조건부 엣지를 가진 노드 이름
        selector: state를 받아 다음 노드의 키를 반환하는 함수
        mapping: 반환된 키에 따라 이동할 노드 이름 매핑
        """
        self.conditional_edges[supervisor_node] = (selector, mapping)

    def get_topological_order(self) -> List[str]:
        in_degree = {n: 0 for n in self.nodes}
        for src, dest_list in self.edges.items():
            for dest in dest_list:
                in_degree[dest] += 1
        queue = [n for n, deg in in_degree.items() if deg == 0]
        topo_order = []
        while queue:
            current = queue.pop(0)
            topo_order.append(current)
            for neighbor in self.edges[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(topo_order) != len(self.nodes):
            raise ValueError("사이클이 존재하거나 위상 정렬 실패.")
        return topo_order

    def run_stream(self, initial_state: GraphState) -> Iterator[Tuple[str, GraphState]]:
        topo_order = self.get_topological_order()
        current_index = 0
        state = initial_state

        print("\n===== Graph Execution (Streaming) 시작 =====\n")
        print("초기 위상 정렬 순서:", topo_order)
        print("\n-------------------------------\n")

        while current_index < len(topo_order):
            node_name = topo_order[current_index]
            node = self.nodes[node_name]
            print(f"==> 노드 실행: {node_name}")
            state = node.process(state)
            print(f"   {node_name} 완료. 현재 state keys: {list(state.keys())}")
            yield node_name, state

            # 조건부 엣지 체크
            if node_name in self.conditional_edges:
                selector, mapping = self.conditional_edges[node_name]
                decision = selector(state)
                print(f"   {node_name} 조건부 결정: {decision}")
                if decision in mapping:
                    next_node = mapping[decision]
                    if next_node == "FINISH":
                        print("   FINISH 결정. 그래프 실행 종료합니다.")
                        break
                    if next_node in topo_order:
                        current_index = topo_order.index(next_node)
                        continue

            # 롤백 체크 (필요 시)
            if "rollback" in state:
                rollback_target = state["rollback"]
                print(f"   [ROLLBACK] {rollback_target} 노드로 돌아갑니다.")
                if rollback_target in topo_order:
                    current_index = topo_order.index(rollback_target)
                    del state["rollback"]
                    continue
                else:
                    print("   [ERROR] 롤백 대상 노드가 존재하지 않습니다.")
            current_index += 1

        print("\n===== Graph Execution 종료 =====\n")
        return state
