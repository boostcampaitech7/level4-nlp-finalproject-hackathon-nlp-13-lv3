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
            {daily_chart}

            다음은 종합 평가 리포트 작성시 주의사항 입니다.
            주의사항1. 핵심 사업 및 경쟁력
            (1)번 기업 분석 리포트와 (2)번 뉴스 리포트의 주요 내용을 활용하여, 기업의 비즈니스 모델과 시장 내 경쟁력을 설명하세요.
            특히 주목할 만한 성장 포인트나 위기 요인이 있다면 구체적으로 서술합니다.
            주의사항2. 거시경제적 환경과 시장 전망
            (3)번 거시경제 분석 리포트를 통해 현재 경제 흐름과 해당 기업 또는 산업 전반에 미치는 영향이 무엇인지 언급하세요.
            금리, 환율, 경기 사이클 등의 거시 지표가 해당 기업 가치에 미치는 영향을 핵심 포인트 위주로 분석합니다.
            주의사항3. 최근 뉴스나 이슈가 가져올 파급효과
            (2)번 뉴스 리포트에서 중요한 이슈나 발표가 있다면, 그것이 기업 실적 또는 이미지에 어떤 영향을 줄 수 있는지 원인-결과 흐름으로 연결 지어 설명하세요.
            시장 심리에 큰 영향을 미치는 이벤트(규제, 정책, 경쟁사 이슈 등)도 함께 고려합니다.
            주의사항4. 재무 상태(재무제표 분석 결과)
            (4)번 재무제표 분석 리포트에서 도출된 가장 중요한 재무 지표(매출, 영업이익, 부채비율, 현금흐름 등)를 중심으로 기업의 재무 건전성과 투자 위험요소를 평가하세요.
            최근 추세와 전년 대비 변화를 간결하게 강조합니다.
            주의사항5. 기술적 분석(호가창/차트) 요약
            (5)번 호가창/차트 분석 리포트를 참고하여, 최근 주가 흐름이나 기술적 지표에서 특별히 눈에 띄는 패턴이나 매수/매도 타이밍 시사점을 제시하세요.
            단순 수치나 차트 신호 나열이 아닌, 실제 투자 판단에 도움이 될 만한 내용을 간략히 정리합니다.

            위의 1~5번 항목에서 도출한 핵심 내용을 유기적으로 연결하여 하나의 종합 리포트를 완성하세요."""
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
        company_report = state.get("financial_report", "")
        news_report = state.get("news_report", "")
        macro_report = state.get("macro_report", "")
        financial_report = state.get("fin_statements_report", "")
        daily_chart_report = state.get("daily_chart_report", "")

        # LLM 호출
        final_answer = self.final_answer_chain.invoke({
            "target": target,
            "company": company_report,
            "news": news_report,
            "macro": macro_report,
            "financial": financial_report,
            "daily_chart": daily_chart_report
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
        "financial_report": "기업 분석 결과 예시",
        "news_report": "뉴스 분석 결과 예시",
        "macro_report": "거시경제 분석 결과 예시",
        "fin_statements_report": "재무제표 분석 결과 예시",
        "daily_chart_report": "차트/호가창 분석 결과 예시",
    }
    final_state = agent.process(test_state)

    print("\n=== 통합 보고서 ===")
    print(final_state.get("integrated_report", "통합 보고서가 생성되지 않았습니다."))
