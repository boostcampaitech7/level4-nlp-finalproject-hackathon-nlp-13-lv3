import os
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph_base에서 Node, GraphState import
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

        # 시스템 프롬프트 (원본 코드대로 유지 가능, 실제 체인에 포함하지 않아도 무방)
        self.system_prompt = SystemMessage(content=(
            "Want assistance provided by qualified individuals enabled with experience on understanding charts "
            "using technical analysis tools while interpreting macroeconomic environment prevailing across world "
            "consequently assisting customers acquire long term advantages requires clear verdicts therefore "
            "seeking same through informed predictions written down precisely! statement contains following content."
        ))

        # 최종 답변 생성을 위한 프롬프트 템플릿 정의
        self.final_prompt_template = PromptTemplate.from_template(
            """다음은 {target}의 주식과 관련된 리포트입니다.
1. 기업 분석 리포트
{company}
2. 뉴스 리포트
{news}
3. 거시경제 분석 리포트
{macro}
4. 재무제표 분석 리포트
{financial}
5. 호가창/차트 분석 리포트
{orderbook}

주어진 리포트를 바탕으로 {target}의 주식에 대한 종합 평가 리포트를 작성해 주세요."""
        )
        # RunnableSequence
        self.final_answer_chain = self.final_prompt_template | self.llm

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph에서 통합 보고서를 생성하는 노드.
        state에 저장된 각 에이전트별 보고서를 모아서, LLM을 통해 'integrated_report'를 작성.
        """
        print(f"[{self.name}] process() 호출")

        target = state.get("company_name", "미지정 기업")
        # 각 에이전트 보고서 가져오기
        company_report = state.get("enterprise_report", "")
        news_report = state.get("news_report", "")
        macro_report = state.get("macro_report", "")
        financial_report = state.get("financial_report", "")
        orderbook_report = state.get("orderbook_report", "")

        # LLM 호출
        final_answer = self.final_answer_chain.invoke({
            "target": target,
            "company": company_report,
            "news": news_report,
            "macro": macro_report,
            "financial": financial_report,
            "orderbook": orderbook_report
        })

        # invoke() 결과가 문자열인지 확인
        if hasattr(final_answer, "content"):
            # 혹은 LLMResult 객체라면 .content 접근
            integrated_text = final_answer.content
        else:
            # 보통 RunnableSequence.invoke()는 최종 문자열 반환
            integrated_text = final_answer

        # state에 통합 보고서 저장
        state["integrated_report"] = integrated_text

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    # standalone 테스트
    agent = ReportIntegrationNode("ReportIntegrationNode")
    test_state: GraphState = {
        "company_name": "LG화학",
        "enterprise_report": "기업 분석 결과 예시",
        "news_report": "뉴스 분석 결과 예시",
        "macro_report": "거시경제 분석 결과 예시",
        "financial_report": "재무제표 분석 결과 예시",
        "orderbook_report": "차트/호가창 분석 결과 예시",
    }
    final_state = agent.process(test_state)

    print("\n=== 통합 보고서 ===")
    print(final_state.get("integrated_report", "통합 보고서가 생성되지 않았습니다."))
