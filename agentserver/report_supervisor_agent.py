from LangGraph_base import Node, GraphState
import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import json

def get_next_node(state: GraphState) -> str:
    """
    현재 상태에서 다음 노드의 식별자를 가져옵니다.

    Args:
        state (GraphState): "next" 키를 포함할 수 있는 현재 상태 사전.

    Returns:
        str: 상태 사전에 "next" 키가 있으면 해당 값을, 없으면 "FINISH"를 반환합니다.
    """
    return state.get("next", "FINISH")

class ReportSupervisorAgent(Node):
    def __init__(self, name: str, quality_threshold: float = 5.0) -> None:
        """
        ReportSupervisorAgent 클래스를 초기화합니다.

        이 함수는 환경변수를 로드하고, 보고서 품질 감독자로서의 역할을 수행하기 위해 필요한 LLM(ChatOpenAI) 인스턴스와
        진단 프롬프트 템플릿을 초기화합니다. 또한, 보고서 품질 임계값(quality_threshold)을 설정합니다.

        Args:
            name (str): 에이전트의 이름.
            quality_threshold (float, optional): 허용 가능한 최소 보고서 품질 점수. 기본값은 5.0입니다.
        """
        load_dotenv()
        super().__init__(name)
        self.quality_threshold = quality_threshold
        
        # LLM 초기화 (진단용)
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.5
        )
        # 시스템 프롬프트: 감독자로서의 역할 설명
        self.system_prompt = SystemMessage(content=(
            "당신은 보고서 품질 감독자입니다. 아래 통합 보고서를 검토하여, "
            "기업 분석, 뉴스, 거시경제, 재무제표, 일월봉 보고서 중 부족한 영역과 그 근거를 "
            "JSON 형식으로 반환하십시오. 예를 들어, 부족하다면 아래와 같이 응답하세요:\n\n"
            "```\n"
            "{\n  \"deficient_area\": \"financial_report\",\n  \"reasons\": \"기업의 핵심 사업 분석이 부족합니다.\"\n}\n"
            "```\n\n"
            "모든 영역이 충분하다면 아래와 같이 응답하세요:\n\n"
            "```\n"
            "{\n  \"deficient_area\": \"ok\",\n  \"reasons\": \"모든 영역이 충분합니다.\"\n}\n"
            "```"
        ))
        # 진단 프롬프트 템플릿 고도화
        self.diagnosis_prompt = PromptTemplate.from_template(
            """다음은 통합 보고서입니다:
            --------------------------------------------------
            {integrated_report}
            --------------------------------------------------

            위 보고서를 검토한 결과, 아래 각 영역에서 반드시 포함되어야 할 내용이 있습니다.

            1. [financial_report]:
            - 기업의 비즈니스 모델, 핵심 사업, 경쟁력, 성장 전략, 주요 위험 요인 및 투자 의견의 근거가 구체적으로 서술되어야 합니다.
            2. [news_report]:
            - 최신 뉴스 이벤트, 발행일 정보, 시계열 변화 및 그에 따른 시사점, 그리고 뉴스가 주가에 미치는 영향이 상세히 분석되어야 합니다.
            3. [macro_report]:
            - 주요 거시경제 지표(예: 환율, 금리 등)의 구체적인 수치와 추세, 해당 지표가 기업에 미치는 영향이 명확히 언급되어야 합니다.
            4. [fin_statements_report]:
            - 주요 재무 비율(예: ROE, ROA, 부채비율 등)과 과거 추세 비교, 재무 건전성 평가가 포함되어야 합니다.
            5. [daily_chart_report]:
            - 주요 기술적 지표(예: 지지선, 저항선, 거래량, RSI, MACD 등)와 가격 전망, 추천 매매 전략이 구체적으로 제시되어야 합니다.

            부족한 영역과 그 이유를 아래 JSON 형식으로 반환해 주세요. 
            예를 들어, 기업 분석 내용이 부족하면:
            ```json
            {
            "deficient_area": "financial_report",
            "reasons": "기업의 핵심 사업 및 경쟁력 분석이 충분하지 않습니다."
            }
            모든 영역이 충분하다면:
            {
            "deficient_area": "ok",
            "reasons": "모든 영역이 충분합니다."
            }
            """
        )
        self.diagnosis_chain = self.diagnosis_prompt | self.llm

    def process(self, state: GraphState) -> GraphState:
        """
        통합 보고서의 품질을 평가하고, 다음 처리 단계(다음 노드)를 결정합니다.

        이 함수는 상태에서 보고서 평가 점수를 확인하여, 점수가 기준 미만인 경우 부족한 영역을 진단합니다.
        재시도 횟수가 3회 이상이거나 점수가 기준 이상이면 다음 노드로 "FinalAnalysisAgent"를 지정합니다.
        만약 보고서 품질이 낮을 경우, 추가 문구를 붙인 통합 보고서를 LLM에 전달하여 부족한 영역과 그 이유를 JSON 형식으로 받아옵니다.
        진단 결과에 따라 부족한 영역에 맞는 다음 노드를 결정하고, 재시도 횟수를 갱신하여 상태에 저장합니다.

        Args:
            state (GraphState): 현재 상태를 나타내는 사전. 이 사전은 "report_score", "integrated_report",
                                "retry_count", "company_name" 등의 키를 포함해야 합니다.

        Returns:
            GraphState: 부족한 영역 진단 결과 및 다음 노드 정보가 업데이트된 상태 사전.
        """
        print(f"[{self.name}] process() 호출 - 감독자 노드 실행")
        
        retry_count = state.get("retry_count", 0)
        if retry_count >= 3:
            print(f"[{self.name}] 재시도 횟수 {retry_count}회 초과. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        score = state.get("report_score")
        if score is None:
            print(f"[{self.name}] 보고서 평가 점수가 없습니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        print(f"[{self.name}] 보고서 평가 점수: {score:.2f} / 10")
        
        if score >= self.quality_threshold:
            print(f"[{self.name}] 보고서 품질 양호합니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        print(f"[{self.name}] 보고서 품질이 낮습니다. 부족한 영역 진단을 시작합니다.")
        integrated_report = state.get("integrated_report", "")
        if not integrated_report:
            print(f"[{self.name}] 통합 보고서가 없습니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        # 재시도 시마다 추가 문구를 붙여 LLM에 변화를 유도
        prompt_suffix = f"\n\n(추가 시도 #{retry_count + 1}: 이전 결과와 동일할 경우, 새로운 관점을 포함해 주세요.)"
        modified_report = integrated_report + prompt_suffix

        diagnosis_response = self.diagnosis_chain.invoke({
            "integrated_report": modified_report
        })
        diagnosis_text = diagnosis_response.content if hasattr(diagnosis_response, "content") else diagnosis_response
        diagnosis_text = diagnosis_text.strip()
        print(f"[{self.name}] 진단 결과: {diagnosis_text}")

        try:
            diagnosis_json = json.loads(diagnosis_text)
            deficient_area = diagnosis_json.get("deficient_area", "ok").lower()
            reasons = diagnosis_json.get("reasons", "")
        except Exception as e:
            print(f"[{self.name}] 진단 결과 JSON 파싱 실패: {e}")
            deficient_area = "final"
            reasons = "진단 결과를 파싱할 수 없습니다."
            
        # 저장: 부족한 영역과 이유를 state에 기록
        state["deficiency_details"] = reasons

        mapping = {
            "financial_report": "FinancialReportsAnalysisAgent",
            "news_report": "NewsAnalysisAgent",
            "macro_report": "MacroeconomicAnalysisAgent",
            "fin_statements_report": "FinancialStatementsAnalysisAgent",
            "daily_chart_report": "DailyChartAnalysisAgent",
            "ok": "FinalAnalysisAgent"
        }
        next_node = mapping.get(deficient_area, "FinalAnalysisAgent")
        if next_node != "FinalAnalysisAgent":
            retry_count += 1
            state["retry_count"] = retry_count
            print(f"[{self.name}] 부족한 영역: {deficient_area} (사유: {reasons}). 재시도 횟수: {retry_count}. 다음 노드: {next_node}")
            state["next"] = next_node
        else:
            print(f"[{self.name}] 모든 영역이 충분합니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    test_state = {
        "report_score": 4,  # 낮은 품질의 예시 점수
        "integrated_report": "### 종합 평가 리포트: LG화학 (LG Chem)\n\n---\n\n#### **1. 핵심 사업 및 경쟁력**\n\n[내용 부족]\n\n---\n\n#### **2. 거시경제적 환경과 시장 전망**\n\n[내용 충분]\n\n---\n\n#### **3. 최근 뉴스나 이슈가 가져올 파급효과**\n\n[내용 충분]\n\n---\n\n#### **4. 재무 상태(재무제표 분석 결과)**\n\n[내용 부족]\n\n---\n\n#### **5. 기술적 분석(호가창/차트) 요약**\n\n[내용 충분]",
        "company_name": "LG화학",
        "retry_count": 0
    }
    supervisor = ReportSupervisorAgent("ReportSupervisorAgent", quality_threshold=5.0)
    test_state = supervisor.process(test_state)
    print("\n최종 상태:")
    print(test_state)
