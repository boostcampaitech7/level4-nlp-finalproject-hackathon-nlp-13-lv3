# fin_reports_analysis_agent.py

import os
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
import time

from LangGraph_base import Node, GraphState 

class FinancialReportsAnalysisAgent(Node):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini", 
            temperature=0.4
        )

        self.system_prompt = SystemMessage(content=(
            "당신은 주식 및 금융 보고서를 분석하는 AI 전문가입니다. 아래 규칙을 반드시 따르세요:\n"
            "1. 반드시 'YYYY년도 MM월 DD일자 OO증권 레포트' 형식으로 날짜와 증권사 출처 정보를 포함할 것.\n"
            "2. 목표 주가, 투자의견 및 관련 정보를 구체적으로 명시할 것.\n"
            "3. 예시: '2024년도 11월 10일자 삼성증권 레포트에 따르면, 목표 주가는 34만 원으로 설정되었습니다.'\n"
            "4. API에서 제공하는 답변을 바탕으로 사용자에게 유익한 주식투자 정보와 함께 반드시 위 형식의 출처 정보를 포함하여 명확하게 설명하세요.\n"
            "5. 투자 정보는 날짜 관계가 매우 중요합니다. 날짜 관계와 정보로부터 추론할 수 있는 인사이트도 제공하세요."
        ))

        self.final_prompt_template = PromptTemplate.from_template(
            "당신은 주식 및 금융 보고서를 분석하는 전문가입니다.\n"
            "아래의 컨텍스트를 바탕으로 반드시 'YYYY년도 MM월 DD일자 OO증권 레포트' 형식의 날짜 및 증권사 출처 정보를 포함하여,\n"
            "목표 주가, 투자의견 등의 구체적인 정보를 명확하게 서술하는 최종 답변을 작성하세요.\n\n"
            "컨텍스트:\n{context}\n\n"
            "질문:\n{question}\n\n"
            "최종 답변을 하기 전에 단계적으로 검토를 진행하세요. 검토의 기준은 현재 상황을 바탕으로 미래의 투자 가치에 대한 인사이트가 구체적이고 명확한지 입니다.\n"
            "최종 답변:"
        )

        self.final_answer_chain = self.final_prompt_template | self.llm

    def call_financial_api(self, query: str) -> str:
        api_url = os.getenv("FINANCIAL_API_URL", "http://localhost:8000/api/query")
        try:
            response = requests.post(api_url, json={"query": query}, timeout=25)
            response.raise_for_status()
            result = response.json()
            return result.get("answer", "답변이 존재하지 않습니다.")
        except Exception as e:
            return f"API 호출 중 오류 발생: {e}"

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph에서 호출되는 메인 함수.
        state에서 "company_name"과 "financial_query"를 읽어 쿼리를 구성하고 LLM 분석을 실행한 후,
        결과를 state["financial_report"]에 저장합니다.
        """
        print(f"[{self.name}] process() 호출")
        
        # 회사명 필수 입력 확인
        company = state.get("company_name", "")
        if not company:
            state["financial_report"] = "회사명이 제공되지 않았습니다."
            return state
        
        # financial_query가 있으면 사용, 없으면 기본 쿼리 생성
        query = state.get("financial_query", f"{company}의 최신 증권 리포트를 분석하여 투자 전략 및 매매의견을 제시해 주세요.")
        
        # API 호출 및 LLM 분석
        api_context = self.call_financial_api(query)
        final_answer = self.final_answer_chain.invoke({"context": api_context, "question": query})
        state["financial_report"] = final_answer.content
        time.sleep(0.5)
        return state

if __name__ == "__main__":
    agent = FinancialReportsAnalysisAgent("FinancialReportsAnalysisAgent")
    test_query = "LG화학의 증권 리포트를 기반으로 한 투자 전망 및 매매의견 분석"
    initial_state: GraphState = {
        "company_name": "LG화학",
        "financial_query": test_query
    }
    final_state = agent.process(initial_state)
    print("\n=== 분석 결과 ===")
    print(final_state.get("financial_report", "결과 없음"))
