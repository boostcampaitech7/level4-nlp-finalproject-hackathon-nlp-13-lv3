# final_analysis_agent.py

import os
import requests
import re
import time

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, Optional

# langchain & prompts
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph
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
            model_name="o1-mini-2024-09-12",  # 예시 모델명 (원본 유지)
            temperature=1,
        )

        # 시스템 프롬프트 (원본 코드)
        self.system_prompt = SystemMessage(content=(
            "Seeking guidance from experienced staff with expertise on financial markets, "
            "incorporating factors such as inflation rate or return estimates along with tracking "
            "stock prices over lengthy period ultimately helping customer understand sector "
            "then suggesting safest possible options available where he/she can allocate funds "
            "depending upon their requirement & interests! question contains following content."
        ))

        # 최종 프롬프트 템플릿 정의 (원본 코드)
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
        """
        LangGraph에서 호출되는 메서드.
        1) company_name, integrated_report, (선택) user_persona 등 읽기
        2) LLM 호출 → JSON 파싱
        3) state["final_opinion"], state["portfolio_suggestion"], state["final_report"] 등에 결과 저장
        4) 실패 시 기본값
        """
        print(f"[{self.name}] process() 호출")

        # 필요한 정보 가져오기
        target = state.get("company_name", "특정 기업")
        report = state.get("integrated_report", "")
        user_persona = state.get("investment_persona", "")  # 기존 코드의 user_persona -> investment_persona 활용

        max_retries = 3
        for attempt in range(max_retries):
            # 프롬프트 생성
            prompt_content = self.final_prompt_template.format(
                target=target,
                report=report,
                user_persona=user_persona
            )
            
            # 모델 호출
            response = self.llm(prompt_content)
            raw_response = response.content if hasattr(response, "content") else response

            try:
                # 응답을 JSON으로 파싱
                cleaned_response = self.extract_json(raw_response)
                parsed_response = InvestmentEvaluation.model_validate_json(cleaned_response)                
                final_output = parsed_response.dict()

                # 성공 시 state에 결과 저장
                state["final_opinion"] = final_output["recommendation"]
                state["portfolio_suggestion"] = final_output["weights"]
                
                # 원한다면 최종 보고서(final_report)도 간단히 작성
                # (여기서는 opinion + suggestion을 합쳐 하나의 문자열로 저장)
                final_report_text = f"최종 매매의견: {final_output['recommendation']}, " \
                                    f"자산 배분 제안: {final_output['weights']}"
                state["final_report"] = final_report_text

                time.sleep(0.5)
                return state

            except Exception as e:
                # 파싱 실패 등 오류
                print(f"[{self.name}] Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    # 최종 실패 시 기본값
                    state["final_opinion"] = "관망"
                    state["portfolio_suggestion"] = "0% 매수/매도"
                    state["error"] = str(e)
                    return state

        return state


if __name__ == "__main__":
    agent = FinalAnalysisAgent("FinalAnalysisAgent")
    # standalone 테스트
    # 예시: state에 integrated_report가 없으면 빈 문자열로 처리
    test_state: GraphState = {
        "company_name": "LG화학",
        "integrated_report": "통합 리포트가 여기 있다고 가정",
        "investment_persona": "중고위험(적극적)"
    }
    final_state = agent.process(test_state)
    print("\n=== 최종 분석 결과 ===")
    print("Final Opinion:", final_state.get("final_opinion"))
    print("Portfolio Suggestion:", final_state.get("portfolio_suggestion"))
    print("Final Report:", final_state.get("final_report"))
    print("Error:", final_state.get("error", "No Error"))
