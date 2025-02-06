import os
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# .env 파일에서 환경변수 로드 (예: OPENAI_API_KEY)
load_dotenv()

# -------------------------
# 1️⃣ 상태(State) 정의
# -------------------------
class ChatState(TypedDict, total=False):
    """LangGraph에서 사용할 상태를 정의하는 클래스"""
    user_message: str         # 사용자가 입력한 질문
    search_results: str       # 검색 결과 저장
    bot_response: str         # 챗봇 응답 저장
    needs_search: bool        # 검색이 필요한지 여부
    correction_attempts: int  # 질문 보정 시도 횟수 (무한 루프 방지)
    relevance_score: str      # 검색 결과 관련성 평가 (추가)

# -------------------------
# 2️⃣ 노드(Node) 함수 정의
# -------------------------
def receive_message(state: ChatState) -> ChatState:
    """
    📌 사용자의 입력을 받아 상태에 저장하는 노드
    """
    state["user_message"] = state.get("user_message", "")
    state["correction_attempts"] = 0  # 보정 시도 횟수 초기화
    return state

def analyze_message(state: ChatState) -> ChatState:
    """
    📌 사용자의 질문을 분석하여 검색이 필요한지 판단하는 노드
    """
    message = state.get("user_message", "").lower()
    state["needs_search"] = "검색" in message  # "검색"이라는 단어가 포함되면 검색 수행
    return state

def perform_search(state: ChatState) -> ChatState:
    """
    📌 문서를 검색하는 노드 (실제 검색 대신 예제 데이터 사용)
    """
    # 검색 결과가 없을 경우, 예제 데이터를 추가
    if state.get("needs_search", False):
        state["search_results"] = "LangGraph는 그래프 기반 RAG를 구현하는 프레임워크입니다."
    else:
        state["search_results"] = ""  # 검색 결과 없음
    return state

def evaluate_results(state: ChatState) -> ChatState:
    """
    📌 검색된 결과가 질문과 관련성이 있는지 평가하는 노드
    """
    if state.get("search_results"):
        state["relevance_score"] = "GOOD"  # 검색 결과가 적절함
    else:
        state["relevance_score"] = "BAD"  # 검색 결과 없음
    return state

def correct_query(state: ChatState) -> ChatState:
    """
    📌 검색 결과가 부족할 경우 질문을 보정하여 다시 검색을 수행하는 노드
    """
    state["correction_attempts"] += 1  # 보정 시도 횟수 증가
    if state["correction_attempts"] > 2:  # 무한 루프 방지
        state["needs_search"] = False  # 더 이상 검색 시도하지 않음
    else:
        state["user_message"] = "LangGraph에 대한 자세한 설명을 검색해주세요."
    return state

def generate_response(state: ChatState) -> ChatState:
    """
    📌 LLM을 사용하여 검색 결과를 바탕으로 답변을 생성하는 노드
    """
    llm = ChatOpenAI(model="gpt-3.5-turbo")  # GPT-3.5 모델 사용
    messages = [
        {"role": "system", "content": "당신은 유용한 정보를 제공하는 챗봇입니다."},
        {"role": "user", "content": state.get("user_message", "")},
    ]
    if state.get("search_results"):
        messages.append({"role": "system", "content": f"검색 결과: {state['search_results']}"})

    # deprecated 된 호출 방식을 invoke로 변경
    response = llm.invoke(messages)
    # 반환된 response가 AIMessage 객체이므로, content 속성을 통해 응답 텍스트를 가져옴
    state["bot_response"] = response.content
    return state


def end_conversation(state: ChatState) -> ChatState:
    """
    📌 대화를 종료하는 노드
    """
    return state

# -------------------------
# 3️⃣ 그래프(Graph) 생성 및 구성
# -------------------------
def create_chatbot_graph() -> StateGraph:
    # ✅ StateGraph 객체 생성
    chatbot_graph = StateGraph(ChatState)

    # ✅ 노드 추가
    chatbot_graph.add_node("receive_message", receive_message)
    chatbot_graph.add_node("analyze_message", analyze_message)
    chatbot_graph.add_node("perform_search", perform_search)
    chatbot_graph.add_node("evaluate_results", evaluate_results)
    chatbot_graph.add_node("correct_query", correct_query)
    chatbot_graph.add_node("generate_response", generate_response)
    chatbot_graph.add_node("end_conversation", end_conversation)

    # ✅ 엣지 추가 (노드 간 연결)
    chatbot_graph.add_edge(START, "receive_message")
    chatbot_graph.add_edge("receive_message", "analyze_message")
    chatbot_graph.add_edge("analyze_message", "perform_search")
    chatbot_graph.add_edge("perform_search", "evaluate_results")

    # ✅ 조건부 엣지 추가 (검색 결과 평가 후 흐름 결정)
    def decide_next_node(state: ChatState) -> str:
        """
        📌 evaluate_results 노드 이후 흐름을 결정하는 조건부 엣지
        """
        if state["relevance_score"] == "BAD" and state["correction_attempts"] < 2:
            return "correct_query"  # 검색 결과가 부적절하면 질문을 수정하여 다시 검색
        return "generate_response"  # 검색 결과가 적절하면 바로 답변 생성

    chatbot_graph.add_conditional_edges(
        "evaluate_results",
        decide_next_node,
        {"correct_query": "correct_query", "generate_response": "generate_response"}
    )

    # ✅ 수정된 질문으로 다시 검색 후 평가
    chatbot_graph.add_edge("correct_query", "perform_search")

    # ✅ 답변 생성 후 종료
    chatbot_graph.add_edge("generate_response", "end_conversation")
    chatbot_graph.add_edge("end_conversation", END)

    # ✅ 그래프 컴파일
    return chatbot_graph.compile()

# -------------------------
# 4️⃣ 그래프 실행
# -------------------------
if __name__ == "__main__":
    # ✅ 초기 상태 설정
    initial_state = {"user_message": "LangGraph에 대해 검색해줘"}

    # ✅ 그래프 생성 및 실행
    compiled_graph = create_chatbot_graph()
    final_state = compiled_graph.invoke(initial_state)

    # ✅ 챗봇의 최종 응답 출력
    print("챗봇 응답:", final_state.get("bot_response", "응답 없음"))
