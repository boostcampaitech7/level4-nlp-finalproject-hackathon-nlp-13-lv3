import os
import requests
from dotenv import load_dotenv

# 최신 권장 방식으로 모듈 임포트
from langchain_openai import ChatOpenAI 
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

class FinancialReportsAnalysisAgent:
    def __init__(self):
        # 환경변수 로드 (.env 파일에 FINANCIAL_API_URL, OPENAI_API_KEY 등이 설정되어 있어야 함)
        load_dotenv()

        # ChatOpenAI 모델 초기화
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini", 
            temperature=0.4
        )

        self.system_prompt = SystemMessage(content=(
            "당신은 주식 및 금융 보고서를 분석하는 AI 전문가입니다. 아래 규칙을 반드시 따르세요:\n"
            "1. 반드시 'YYYY년도 MM월 DD일자 OO증권 레포트' 형식으로 날짜와 증권사 출처 정보를 포함할 것.\n"
            "2. 목표 주가, 투자의견 및 관련 정보를 구체적으로 명시할 것.\n"
            "3. 예시: '2024년도 11월 10일자 삼성증권 레포트에 따르면, 목표 주가는 34만 원으로 설정되었습니다.'\n"
            "4. API에서 제공하는 답변을 바탕으로 사용자에게 유익한 주식투자 정보와 함께 반드시 위 형식의 출처 정보를 포함하여 명확하게 설명하세요. "
            "5. 투자 정보는 날짜 관계가 매우 중요합니다. 날짜 관계와 정보로 부터 추론할 수 있는 인사이트도 제공하세요."
        ))

        # 최종 답변 생성을 위한 프롬프트 템플릿 정의
        self.final_prompt_template = PromptTemplate.from_template(
            "당신은 주식 및 금융 보고서를 분석하는 전문가입니다.\n"
            "아래의 컨텍스트를 바탕으로 반드시 'YYYY년도 MM월 DD일자 OO증권 레포트' 형식의 날짜 및 증권사 출처 정보를 포함하여,\n"
            "목표 주가, 투자의견 등의 구체적인 정보를 명확하게 서술하는 최종 답변을 작성하세요.\n\n"
            "컨텍스트:\n{context}\n\n"
            "질문:\n{question}\n\n"
            "최종 답변을 하기 전에 단계적으로 검토를 진행하세요. 검토의 기준은 현재 상황을 바탕으로 미래의 투자 가치에 대한 인사이트가 구체적이고 명확한지 입니다.\n"
            "최종 답변:"
        )

        # RunnableSequence
        self.final_answer_chain = self.final_prompt_template | self.llm

    def call_financial_api(self, query: str) -> str:
        """
        주어진 query를 재무 분석 API에 전송하여 응답에서 answer를 반환합니다.
        API URL은 환경변수 FINANCIAL_API_URL에서 가져오며, 기본값은 http://localhost:8000/api/query 입니다.
        """
        api_url = os.getenv("FINANCIAL_API_URL", "http://localhost:8000/api/query")
        try:
            response = requests.post(api_url, json={"query": query}, timeout=25)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            result = response.json()      # 예상 응답 형식: {"context": [...], "answer": "분석 결과"}
            return result.get("answer", "답변이 존재하지 않습니다.")
        except Exception as e:
            return f"API 호출 중 오류 발생: {e}"

    def run(self, query: str) -> str:
        """
        Agent의 메인 실행 함수.
        1. 재무 분석 API를 호출하여 원본 분석 결과(컨텍스트)를 가져옵니다.
        2. 최종 답변 체인을 통해 원하는 형식의 답변을 생성하여 반환합니다.
        """
        # API 호출하여 원본 컨텍스트 얻기
        api_context = self.call_financial_api(query)
        # 최종 답변 생성 
        final_answer = self.final_answer_chain.invoke({"context": api_context, "question": query})
        return final_answer

# 모듈 테스트 또는 standalone 실행 시 사용
if __name__ == "__main__":
    agent = FinancialReportsAnalysisAgent()
    test_query = "2025년 3월쯤 네이버에 주식 투자를 하려고해. 전문가 및 증권사들의 의견을 참고해서 인사이트를 제공해줘."
    answer = agent.run(test_query)
    print("최종 답변:", answer)
