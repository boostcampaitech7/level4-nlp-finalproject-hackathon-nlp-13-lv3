# fin_Financial_Statements_agent.py

import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph_base에서 Node, GraphState import (에이전트 구조)
from LangGraph_base import Node, GraphState


class FinancialStatementsAnalysisAgent(Node):
    """
    재무제표 분석 에이전트:
    1) 특정 기업명의 재무제표 데이터를 수집/스크래핑/가공
    2) 각 항목(건전성, 수익성, 성장성, 유동성, 활동성 등)으로 분류
    3) LLM에 전달하여 종합 투자 보고서(재무제표 기반)를 생성
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()

        # LLM 초기화 (모델명, 온도 등 필요 시 조정)
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.5
        )

        # 재무제표 분석 전문가 역할 시스템 프롬프트
        self.system_prompt = SystemMessage(content=(
            "당신은 재무제표를 심층 분석하여 주식 투자 가치를 평가하는 전문가입니다. 다음 규칙을 따르세요:\n"
            "1. 건전성(부채비율 등), 수익성(ROE, ROA 등), 성장성(매출·영업이익 증가율), "
            "유동성(유동비율), 활동성(재고 회전율 등) 지표를 확인하세요.\n"
            "2. 각 지표가 해당 기업의 최근 몇 년(예: 3년) 또는 분기별 추세에서 어떻게 변화했는지 파악하세요.\n"
            "3. 분석 결과는 'YYYY년도 MM월 DD일자 재무제표 분석' 형식으로 날짜와 출처(가상의 증권사 등)를 포함하세요.\n"
            "4. 분석 근거(재무제표 데이터)와 함께 투자 의견(매수/매도/관망)을 제시하세요.\n"
            "5. 향후 리스크 요인과 추가 확인해야 할 항목이 있다면 함께 언급하세요."
        ))

        # 최종 프롬프트 템플릿: 
        # 파이썬의 PromptTemplate.from_template를 이용, 
        # 재무제표 데이터를 컨텍스트로, 질문(=분석 요청)을 포맷
        self.final_prompt_template = PromptTemplate.from_template(
            "아래는 특정 기업의 최근 재무제표 데이터입니다. "
            "각 항목(건전성, 수익성, 성장성, 유동성, 활동성)으로 요약했으니 분석해주세요.\n\n"
            "재무제표 데이터:\n{fs_data}\n\n"
            "분석 요청:\n{question}\n\n"
            "아래 단계로 분석을 진행하세요:\n"
            "1. 건전성(부채비율 등) 평가\n"
            "2. 수익성(ROE/ROA 등) 및 성장성(매출·영업이익 증가율) 평가\n"
            "3. 유동성(유동비율), 활동성(회전율 등) 평가\n"
            "4. 종합 투자 의견 및 리스크 요인\n\n"
            "분석 결과:"
        )
        self.final_answer_chain = self.final_prompt_template | self.llm

    def fetch_financial_statements(self, company_name: str) -> dict:
        """
        재무제표 데이터 수집/스크래핑/가공 (예시로 간단히 고정 데이터 반환).
        실제 구현에서는 requests + BeautifulSoup, 혹은 API 호출로 데이터 불러올 수 있음.
        """
        ## 갑작스러운 dart 점검으로 인해.. 
        # 예시: 임의의 데이터 (연도별, 혹은 분기별로 구분)
        # 실제로는 스크래핑/API로 수집한 뒤, JSON 형태로 가공
        sample_fs = {
            "건전성": {
                "부채비율": "85%",
                "이자보상배율": "10배"
            },
            "수익성": {
                "ROE": "12%",
                "ROA": "7%",
                "영업이익률": "15%"
            },
            "성장성": {
                "매출증가율": "10%",
                "영업이익증가율": "12%"
            },
            "유동성": {
                "유동비율": "130%",
                "당좌비율": "85%"
            },
            "활동성": {
                "재고자산회전율": "5회/년",
                "총자산회전율": "1.2배/년"
            }
        }
        return sample_fs

    def format_financial_statements(self, fs_data: dict) -> str:
        """
        재무제표 데이터를 문자열로 가공:
        건전성, 수익성, 성장성, 유동성, 활동성 섹션별로 표시
        """
        formatted = f"기업명: {self.current_company}\n"
        for category, values in fs_data.items():
            formatted += f"\n[{category}]\n"
            for item, val in values.items():
                formatted += f"{item}: {val}\n"
        return formatted

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드 인터페이스 구현:
        1) state에서 company_name 가져옴
        2) 재무제표 데이터 수집/포맷
        3) LLM 분석 호출
        4) 결과를 state['financial_statements_report'] 등에 저장
        """
        print(f"[{self.name}] process() 호출")

        company = state.get("company_name", "Unknown")
        self.current_company = company  # 문자열 포맷팅에 사용

        # 간단히 'fs_query' 같은 질의키를 사용하거나, 고정된 질문 사용 가능
        question = "위 재무제표를 기반으로 투자 의견을 제시해주세요."

        # 1) 재무제표 데이터 수집
        fs_data = self.fetch_financial_statements(company)
        # 2) 문자열로 포맷
        formatted_fs = self.format_financial_statements(fs_data)

        # 3) LLM 분석
        final_answer = self.final_answer_chain.invoke({
            "fs_data": formatted_fs,
            "question": question
        })

        # 4) 결과 저장 (예: 'financial_statements_report' 키)
        state["financial_statements_report"] = final_answer.content

        time.sleep(0.5)
        return state


if __name__ == "__main__":
    # standalone 테스트 예시
    agent = FinancialStatementsAnalysisAgent("FinancialStatementsAnalysisAgent")
    test_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(test_state)

    print("\n=== 재무제표 분석 결과 ===")
    print(final_state.get("financial_statements_report", "분석 결과 없음"))
