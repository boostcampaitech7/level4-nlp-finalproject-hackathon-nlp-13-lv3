# report_integration_agent.py

import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph_base에서 Node, GraphState import
from LangGraph_base import Node, GraphState

load_dotenv()

class ReportIntegrationNode(Node):
    """
    주식 보고서 통합 에이전트:
    여러 분야의 리포트(기업 분석, 뉴스, 거시경제, 재무제표, 호가창/차트)를 종합하여
    하나의 완성도 높은 통합 보고서를 생성하는 역할을 수행합니다.
    """
    
    def __init__(self, name: str) -> None:
        """
        에이전트 초기화 함수.

        이 함수는 에이전트의 이름을 설정하고, LLM(ChatOpenAI) 인스턴스를 초기화하며,
        주식 보고서 통합 전문가로서의 시스템 프롬프트와 최종 프롬프트 템플릿을 설정합니다.

        Args:
            name (str): 에이전트의 이름
        """
        super().__init__(name)
        
        # LLM 초기화 (시스템 프롬프트 포함)
        self.llm = ChatOpenAI(
            model_name="o1-mini-2024-09-12",
            temperature=1
        )
        # 시스템 프롬프트: 통합 보고서를 작성하는 전문가로서의 역할을 명시
        self.system_prompt = SystemMessage(content=(
            "당신은 주식 보고서 통합 전문가입니다. 각 분야의 보고서(기업 분석, 뉴스, 거시경제, 재무제표, 호가창/차트)를 종합하여 하나의 완성도 높은 통합 보고서를 작성해야 합니다. "
            "만약 특정 영역에 부족함이 있다면, 그 부족한 부분을 보완할 수 있도록 추가 정보를 요청하거나, 그 영역에 집중하여 분석 결과를 개선해야 합니다."
        ))
        # 최종 프롬프트 템플릿: deficiency_details가 있는 경우 이를 프롬프트에 추가하여 보완 요청을 포함
        self.final_prompt_template = PromptTemplate.from_template(
            """다음은 {target}의 주식과 관련된 리포트입니다.
            
            1. 기업 분석 리포트:
            {company}

            2. 뉴스 리포트:
            {news}

            3. 거시경제 분석 리포트:
            {macro}

            4. 재무제표 분석 리포트:
            {financial}

            5. 호가창/차트 분석 리포트:
            {daily_chart}

            {deficiency}

            위의 각 보고서를 종합하여 하나의 통합 보고서를 작성해 주세요.
            """
        )
        # RunnableSequence: 프롬프트 템플릿과 LLM 모델을 연결
        self.final_answer_chain = self.final_prompt_template | self.llm

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드 인터페이스를 구현하는 함수로, 
        여러 리포트 데이터를 통합하여 하나의 완성도 높은 주식 보고서를 생성합니다.

        1. state로부터 필요한 리포트 데이터를 추출합니다.
        2. deficiency_details가 존재하는 경우, 이를 보완 요청 텍스트로 포함합니다.
        3. 최종 프롬프트를 구성하고 LLM을 호출하여 통합 보고서를 생성합니다.
        4. 생성된 통합 보고서를 state에 저장합니다.

        Args:
            state (GraphState): 에이전트 실행 시 전달되는 상태 정보 dictionary.
                필요한 키: 'company_name', 'financial_report', 'news_report',
                'macro_report', 'fin_statements_report', 'daily_chart_report', 'deficiency_details' (선택)

        Returns:
            GraphState: 생성된 통합 보고서가 포함된 업데이트된 상태 정보.
        """
        print(f"[{self.name}] process() 호출")
        
        # 필수 정보 가져오기
        target = state.get("company_name", "미지정 기업")
        company_report = state.get("financial_report", "")
        news_report = state.get("news_report", "")
        macro_report = state.get("macro_report", "")
        financial_report = state.get("fin_statements_report", "")
        daily_chart_report = state.get("daily_chart_report", "")
        
        # 부족한 영역에 대한 상세 정보가 있으면 프롬프트에 추가
        deficiency_details = state.get("deficiency_details", "")
        if deficiency_details:
            deficiency_text = "[보완 요청 사항]: " + deficiency_details
        else:
            deficiency_text = ""
        
        # 최종 프롬프트 생성 시, deficiency 정보도 전달
        prompt_values = {
            "target": target,
            "company": company_report,
            "news": news_report,
            "macro": macro_report,
            "financial": financial_report,
            "daily_chart": daily_chart_report,
            "deficiency": deficiency_text
        }
        
        final_answer = self.final_answer_chain.invoke(prompt_values)
        # 결과를 state에 저장
        state["integrated_report"] = final_answer.content
        
        time.sleep(0.5)
        return state

if __name__ == "__main__":
    # standalone 테스트 예시
    test_state: GraphState = {
        "company_name": "LG화학",
        "financial_report": "기업 분석 결과 예시",
        "news_report": "뉴스 분석 결과 예시",
        "macro_report": "거시경제 분석 결과 예시",
        "fin_statements_report": "재무제표 분석 결과 예시",
        "daily_chart_report": "호가창/차트 분석 결과 예시",
        # deficiency_details가 있으면 보완 요청 내용이 프롬프트에 추가됩니다.
        "deficiency_details": "기업 분석 리포트에 핵심 사업 및 경쟁력 분석이 부족합니다."
    }
    agent = ReportIntegrationNode("ReportIntegrationNode")
    final_state = agent.process(test_state)
    
    print("\n=== 통합 보고서 ===")
    print(final_state.get("integrated_report", "통합 보고서가 생성되지 않았습니다."))
