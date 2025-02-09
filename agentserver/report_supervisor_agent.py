# report_supervisor_agent.py

from LangGraph_base import Node, GraphState
import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import json

def get_next_node(state: GraphState) -> str:
    return state.get("next", "FINISH")

class ReportSupervisorAgent(Node):
    def __init__(self, name: str, quality_threshold: float = 5.0) -> None:
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

            위 보고서를 검토한 결과, 아래 5개 영역 중 어느 부분이 부족한지와 그 근거를 도출해 주세요.
            - financial_report (증권리포트 기반 기업 분석 보고서)
            - news_report (뉴스 분석 보고서)
            - macro_report (거시경제 분석 보고서)
            - fin_statements_report (재무제표 분석 보고서)
            - daily_chart_report (호가창/차트 분석 보고서)

            부족한 부분과 그 이유를 JSON 형식으로 반환해 주세요. 만약 모든 영역이 충분하다면, deficient_area는 "ok"로 응답하십시오.
            """
        )
        self.diagnosis_chain = self.diagnosis_prompt | self.llm

    def process(self, state: GraphState) -> GraphState:
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

        diagnosis_response = self.diagnosis_chain.invoke({
            "integrated_report": integrated_report
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