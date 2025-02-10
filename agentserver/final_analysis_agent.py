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
    """
    LLM의 투자 분석 결과를 구조화하는 Pydantic 모델입니다.

    Attributes:
        recommendation (Literal["매수", "매도", "관망"]): 투자 추천 방향
        weights (str): 자본 배분 비율 제안
            예: "사용 가능한 자본의 30% 매수"

    Note:
        JSON 형식의 LLM 응답을 파싱하고 검증하는데 사용됩니다.
    """
    
    recommendation: Literal["매수", "매도", "관망"] = Field(
        ..., description="주식 투자 추천 방향 (매수, 매도, 관망 중 하나)"
    )
    weights: str = Field(
        ..., description="매수/매도 의견에 대해 현재 자본을 사용할 비율 (예: 사용 가능한 자본의 5% 매수, 사용 가능한 자본의 80% 매도)"
    )

class FinalAnalysisAgent(Node):
    """
    모든 분석 결과를 종합하여 최종 투자 결정을 내리는 에이전트입니다.

    통합 리포트를 분석하여 매수/매도/관망 결정과 함께
    구체적인 자본 배분 전략을 제시합니다.

    Attributes:
        name (str): 에이전트의 이름
        llm (ChatOpenAI): 최종 분석에 사용되는 LLM 모델 (o1-mini)
        system_prompt (SystemMessage): LLM에 제공되는 시스템 프롬프트
        final_prompt_template (PromptTemplate): 최종 분석을 위한 프롬프트 템플릿

    Note:
        - temperature=1로 설정되어 있어 다양한 투자 전략을 제시할 수 있습니다.
        - 최대 3번의 재시도를 통해 안정적인 결과를 보장합니다.
    """
    
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
        """
        LLM 응답에서 JSON 형식의 데이터를 추출합니다.

        Args:
            raw_response (str): LLM의 원본 응답 텍스트

        Returns:
            str: 추출된 JSON 문자열
                마크다운 코드 블록이 있는 경우 해당 부분만 추출
                없는 경우 원본 응답 반환

        Note:
            정규식을 사용하여 ```json ... ``` 형식의 코드 블록을 처리합니다.
        """
        
        # 마크다운 코드 블록이 있는 경우 해당 부분만 추출
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_response, re.DOTALL)
        if match:
            return match.group(1)
        return raw_response

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드로서 최종 투자 분석을 수행합니다.

        Args:
            state (GraphState): 현재 그래프의 상태
                필요한 키:
                - company_name: 분석 대상 기업명
                - integrated_report: 통합 분석 리포트
                선택적 키:
                - investment_persona: 투자자 성향

        Returns:
            GraphState: 업데이트된 상태
                추가되는 키:
                - final_opinion: 최종 매매 의견 ("매수"/"매도"/"관망")
                - portfolio_suggestion: 자본 배분 제안
                - final_report: 최종 보고서 문자열
                실패 시:
                - error: 오류 메시지

        Note:
            - 최대 3번의 재시도를 수행합니다.
            - 모든 시도 실패 시 기본값 ("관망", "0% 매수/매도")을 반환합니다.
            - JSON 파싱 실패 시 에러 메시지를 포함합니다.

        Example:
            >>> state = {
            ...     "company_name": "LG화학",
            ...     "integrated_report": "리포트 내용...",
            ...     "investment_persona": "중고위험(적극적)"
            ... }
            >>> result = agent.process(state)
            >>> print(result["final_opinion"])  # "매수"
            >>> print(result["portfolio_suggestion"])  # "사용 가능한 자본의 30% 매수"
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
