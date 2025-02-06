import os
import requests
import re

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 최신 권장 방식으로 모듈 임포트
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

from typing import Literal

from LangGraph_base import Node, GraphState 

class InvestmentEvaluation(BaseModel):
    recommendation: Literal["매수", "매도", "관망"] = Field(
        ..., description="주식 투자 추천 방향 (매수, 매도, 관망 중 하나)"
    )
    weights: str = Field(
        ..., description="매수/매도 의견에 대해 현재 자본을 사용할 비율 (예: 사용 가능한 자본의 5% 매수, 사용 가능한 자본의 80% 매도)"
    )

class FinalAnalysisAgent(Node):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()

        # LLM 초기화
        self.llm = ChatOpenAI(
            model_name="o1-mini-2024-09-12",
            temperature=1,
        )

        self.system_prompt = SystemMessage(content=(
            "Seeking guidance from experienced staff with expertise on financial markets, incorporating factors such as inflation rate or return estimates along with tracking stock prices over lengthy period ultimately helping customer understand sector then suggesting safest possible options available where he/she can allocate funds depending upon their requirement & interests! question contains following content."
        ))

        # 프롬프트 템플릿 정의
        self.final_prompt_template = PromptTemplate.from_template(
        """다음은 {target}의 주식과 관련된 리포트입니다.
        {report}

        {user_persona}
        반드시 아래 JSON 형식으로만 답변하세요. 다른 설명은 절대 추가하지 마세요:
        {{
            "recommendation": "매수/매도/관망 중 하나",
            "weights": "사용 가능한 자본의 X% 매수/매도"
        }}"""
        )

    def extract_json(self, raw_response: str) -> str:
        # 마크다운 코드 블록이 있는 경우 해당 부분만 추출
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_response, re.DOTALL)
        if match:
            return match.group(1)
        return raw_response

    def process(self, state: GraphState) -> GraphState:
        target = state.get("company_name")
        report = state.get("integrated_report")
        user_persona = state.get("user_persona")
        
        max_retries = 3
        for attempt in range(max_retries):
            # 프롬프트 생성
            prompt = self.final_prompt_template.format(target=target, report=report, user_persona=user_persona)

            # 모델 호출 및 응답 받기
            response = self.llm(prompt)

            # 응답 검증 및 파싱
            try:
                raw_response = response.content if hasattr(response, "content") else response
                cleaned_response = self.extract_json(raw_response)
                parsed_response = InvestmentEvaluation.model_validate_json(cleaned_response)
                final_output = parsed_response.dict()

                state["final_opinion"] = final_output["recommendation"]
                state["portfolio_suggestion"] = final_output["weight"]

                return state
            except Exception as e:
                #print(f"Attempt {attempt+1} failed with error: {e}")
                if attempt == max_retries - 1:
                # 에러 발생 시 기본값 반환 또는 에러 처리
                    return {
                        "recommendation": "관망",
                        "weights": "0% 매수/매도",
                        "error": str(e),
                    }
if __name__ == "__main__":
    agent = FinalAnalysisAgent("FinalAnalysisAgent")
    test_query = "해당 기업의 뉴스가 주식시장에 미치는 영향 분석"
    initial_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(initial_state)
    print("\n===  분석 결과 ===")
    print(final_state.get("news_analysis", "결과 없음"))