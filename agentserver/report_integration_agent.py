import os
import requests

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 최신 권장 방식으로 모듈 임포트
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

from typing import Literal

import time

from LangGraph_base import Node, GraphState 

class ReportIntegrationNode(Node):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()

        # ChatOpenAI 모델 초기화
        self.llm = ChatOpenAI(
            model_name="o1-mini-2024-09-12",
            temperature=1
            )
        self.system_prompt = SystemMessage(content=(
            "Want assistance provided by qualified individuals enabled with experience on understanding charts using technical analysis tools while interpreting macroeconomic environment prevailing across world consequently assisting customers acquire long term advantages requires clear verdicts therefore seeking same through informed predictions written down precisely! statement contains following content."
        ))
        # 최종 답변 생성을 위한 프롬프트 템플릿 정의
        self.final_prompt_template = PromptTemplate.from_template(
            """다음은 {target}의 주식과 관련된 리포트입니다.
            1.기업 분석 리포트
            {company}
            2.뉴스 리포트
            {news}
            3.거시경제 분석 리포트
            {marco}
            4.재무제표 분석 리포트
            {financial}
            5.호가창 리포트
            {orderbook}


            주어진 리포트를 바탕으로 {target}의 주식에 대한 종합 평가 리포트를 작성해 주세요."""
            )
        # RunnableSequence
        self.final_answer_chain = self.final_prompt_template | self.llm

    def process(self, state: GraphState) -> GraphState:
        # 최종 답변 생성
        target = state.get("company_name")
        company = state.get("enterprise_report")
        news = state.get("news_report")
        marco = state.get("macro_report")
        financial = state.get("financial_report")
        orderbook = state.get("orderbook_report")

        final_answer = self.final_answer_chain.invoke({"target": target, "company": company, "news":news,"marco":marco,"financial":financial, "orderbook":orderbook})
        state["integrated_report"]=final_answer

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    agent = ReportIntegrationNode("ReportIntergrationNode")
    test_query = "해당 기업의 뉴스가 주식시장에 미치는 영향 분석"
    initial_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(initial_state)
    print("\n===  분석 결과 ===")
    print(final_state.get("news_analysis", "결과 없음"))