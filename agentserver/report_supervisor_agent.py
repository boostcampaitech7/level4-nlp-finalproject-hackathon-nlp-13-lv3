# report_supervisor_agent.py

from LangGraph_base import Node, GraphState
import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

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
        # 시스템 프롬프트: 통합 보고서를 읽고 부족한 영역(5개 영역 중 하나)을 단일 키워드로 반환하도록 지시
        self.system_prompt = SystemMessage(content=(
            "당신은 보고서 품질 감독자입니다. 아래 통합 보고서를 읽고, "
            "기업 분석, 뉴스, 거시경제, 재무제표, 일월봉 보고서 중에서 부족한 부분이 있다면 "
            "해당 영역의 키워드를 하나만 반환하세요. 부족한 부분이 없으면 'OK'라고 답변하세요."
        ))
        # 진단 프롬프트 템플릿
        self.diagnosis_prompt = PromptTemplate.from_template(
            """다음은 통합 보고서입니다:
{integrated_report}

어느 부분이 부족합니까? 선택 가능한 영역은:
- financial_report
- news_report
- macro_report
- fin_statements_report
- daily_chart_report

부족한 부분이 없으면 'OK'라고 답변하세요."""
        )
        # 진단 체인 구성 (프롬프트 템플릿과 LLM 모델 연결)
        self.diagnosis_chain = self.diagnosis_prompt | self.llm

    def process(self, state: GraphState) -> GraphState:
        print(f"[{self.name}] process() 호출 - 감독자 노드 실행")
        
        # 최대 재시도 횟수 체크
        retry_count = state.get("retry_count", 0)
        if retry_count >= 3:
            print(f"[{self.name}] 재시도 횟수 {retry_count}회 초과. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        # report_score가 fin_report_scorer_agent에서 저장되어 있다고 가정
        score = state.get("report_score")
        if score is None:
            print(f"[{self.name}] 보고서 평가 점수가 없습니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        print(f"[{self.name}] 보고서 평가 점수: {score:.2f} / 10")

        # 점수가 기준(quality_threshold) 이상이면 품질 양호로 판단
        if score >= self.quality_threshold:
            print(f"[{self.name}] 보고서 품질 양호합니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"
            return state

        # 점수가 미만이면 부족한 영역을 진단 (진단용 LLM 사용)
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
        diagnosis_text = diagnosis_text.strip().lower()
        print(f"[{self.name}] 진단 결과: {diagnosis_text}")

        # 매핑: 진단 결과에 따라 해당 에이전트 이름 반환
        mapping = {
            "financial_report": "FinancialReportsAnalysisAgent",
            "news_report": "NewsAnalysisAgent",
            "macro_report": "MacroeconomicAnalysisAgent",
            "fin_statements_report": "FinancialStatementsAnalysisAgent",
            "daily_chart_report": "DailyChartAnalysisAgent",
            "ok": "FinalAnalysisAgent"
        }
        next_node = mapping.get(diagnosis_text, "FinalAnalysisAgent")
        if next_node != "FinalAnalysisAgent":
            retry_count += 1
            state["retry_count"] = retry_count
            print(f"[{self.name}] 부족한 영역: {diagnosis_text}. 재시도 횟수: {retry_count}. 다음 노드: {next_node}")
            state["next"] = next_node
        else:
            print(f"[{self.name}] 보고서 품질 양호합니다. FINISH 처리합니다.")
            state["next"] = "FinalAnalysisAgent"

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    test_state = {
        "report_score": 6,  # 예시 점수 4점 (품질 미달)
        "integrated_report": "예시 통합 보고서 텍스트. 내용이 부족합니다.",
        "company_name": "LG화학",
        "retry_count": 0
    }
    supervisor = ReportSupervisorAgent("ReportSupervisorAgent", quality_threshold=5.0)
    test_state = supervisor.process(test_state)
    print("\n최종 상태:")
    print(test_state)
