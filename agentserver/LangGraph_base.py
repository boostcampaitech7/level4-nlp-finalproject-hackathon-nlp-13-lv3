# LangGraph_base.py

from typing import Annotated, List, Tuple, Iterator
from typing_extensions import TypedDict
import time

# GraphState: 모든 노드가 공유하는 상태를 정의합니다.
class GraphState(TypedDict, total=False):
    company_name: Annotated[str, "분석 대상 기업명"]
    user_assets: Annotated[float, "사용자 보유 자산"]

    # (새로 추가) 투자 성향 페르소나
    investment_persona: Annotated[str, "사용자의 투자 성향 (저위험/중위험/중고위험/고위험)"]

    # 각 에이전트별 보고서
    enterprise_report: Annotated[str, "기업 분석 보고서"]
    news_report: Annotated[str, "뉴스 및 감성 분석 보고서"]
    macro_report: Annotated[str, "거시경제 분석 보고서"]
    financial_report: Annotated[str, "재무제표 분석 보고서"]
    orderbook_report: Annotated[str, "호가창 분석 보고서"]

    # 통합 보고서
    integrated_report: Annotated[str, "통합 보고서"]

    # 최종 분석 결과
    final_opinion: Annotated[str, "최종 매매의견"]
    portfolio_suggestion: Annotated[str, "자산 배분 제안"]

    # 최종 산출물
    final_report: Annotated[str, "최종 보고서"]

    # 롤백 요청 (체크포인트)
    rollback: Annotated[str, "롤백 대상 노드 이름"]


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

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node
        if node.name not in self.edges:
            self.edges[node.name] = []

    def add_edge(self, source: str, destination: str) -> None:
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Source 또는 Destination 노드가 그래프에 존재하지 않습니다.")
        self.edges[source].append(destination)

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
## 스트리밍 처리 수정 예정
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

            if "rollback" in state:
                rollback_target = state["rollback"]
                print(f"  [ROLLBACK] {rollback_target} 노드로 돌아갑니다.")
                if rollback_target in topo_order:
                    current_index = topo_order.index(rollback_target)
                    del state["rollback"]
                    continue
                else:
                    print("  [ERROR] 롤백 대상 노드가 존재하지 않습니다.")
            current_index += 1

        print("\n===== Graph Execution 종료 =====\n")
        return state
