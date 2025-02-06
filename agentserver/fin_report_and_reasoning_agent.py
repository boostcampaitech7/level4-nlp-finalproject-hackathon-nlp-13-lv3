import os
import requests
import re

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 최신 권장 방식으로 모듈 임포트
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from typing import Literal

#from ~~ 사용자 점수 함수
#from financial_reports_analysis_agent import FinancialReportsAnalysisAgent
#from 뉴스리포트 import ~~
#from 호가창리포트 import ~~

#fin = FinancialReportsAnalysisAgent()
#뉴스 = ~~1()
#호가창 = ~~2()
#query = "네이버 주식 관련 리포트를 작성해줘"

#target = "삼성"
#answer_fin = fin.run(query)
#answer_news = ~~1.run(query)
#answer_ord = ~~2.run(query)

#company = answer_fin.content
#news = answer_news.content
#orderbook = answer_ord.content

class Financial_Analyst:
    def __init__(self):
        # 환경변수 로드 (.env 파일에 FINANCIAL_API_URL, OPENAI_API_KEY 등이 설정되어 있어야 함)
        load_dotenv()

        # ChatOpenAI 모델 초기화
        self.llm = ChatOpenAI(
            model_name="o1-mini-2024-09-12",
            temperature=1
            )
        self.system_prompt = SystemMessage(content=(
            "Want assistance provided by qualified individuals enabled with experience on understanding charts using technical analysis tools while interpreting macroeconomic environment prevailing across world consequently assisting customers acquire long term advantages requires clear verdicts therefore seeking same through informed predictions written down precisely! statement contains following content."
        ))
        # 최종 답변 생성을 위한 프롬프트 템플릿 정의
        self.final_prompt_template = PromptTemplate.from_template(
            """다음은 {target}의 주식과 관련된 리포트입니다.
            1.기업 분석 리포트
            {company}
            2.뉴스 리포트
            {news}
            3.호가창 리포트
            {orderbook}

            주어진 리포트를 바탕으로 {target}의 주식에 대한 종합 평가 리포트를 작성해 주세요."""
            )
        # RunnableSequence
        self.final_answer_chain = self.final_prompt_template | self.llm

    def run(self, target:str, company:str, news:str, orderbook:str ) -> str:
        # 최종 답변 생성
        final_answer = self.final_answer_chain.invoke({"target": target, "company": company, "news":news, "orderbook":orderbook})
        return final_answer

class InvestmentEvaluation(BaseModel):
    recommendation: Literal["매수", "매도", "관망"] = Field(
        ..., description="주식 투자 추천 방향 (매수, 매도, 관망 중 하나)"
    )
    weights: str = Field(
        ..., description="매수/매도 의견에 대해 현재 자본을 사용할 비율 (예: 사용 가능한 자본의 5% 매수, 사용 가능한 자본의 80% 매도)"
    )

class Investment_Manager:
    def __init__(self):
        # 환경 변수 로드
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

    def run(self, target: str, report: str, user_persona:str) -> dict:
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
                return parsed_response.dict()
            except Exception as e:
                #print(f"Attempt {attempt+1} failed with error: {e}")
                if attempt == max_retries - 1:
                # 에러 발생 시 기본값 반환 또는 에러 처리
                    return {
                        "recommendation": "관망",
                        "weights": "0% 매수/매도",
                        "error": str(e),
                    }

# 모듈 테스트 또는 standalone 실행 시 사용
if __name__ == "__main__":
    agent1 = Financial_Analyst()
    agent2 = Investment_Manager()
    #target, company, news, orderbook 불러오는 함수 필요
    target="네이버" # web에서 선택한 기업 정보 가져오기
    company="네이버는 발전 가능성이 약간 있다." #한택님 에이전트 출력
    news="네이버 주식은 조금 올라갔다." #현풍님 에이전트 출력
    orderbook="네이버 주식은 적당하게 평가 되어있다." #정인님 에이전트 출력

    #사용자 점수 기반 프롬프트 함수로 0,1,2,3선정
    user_persona=[
        "사용자는 저위험(보수적) 투자자이므로, 수익률은 적어도 리스크가 적은 우량 주식에 관심이 많습니다.", 
        "사용자는 중위험(중립적) 투자자이므로, 약간의 리스크로 평균적인 수익을 얻을 수 있는 주식에 관심이 많습니다.",
        "사용자는 중고위험(적극적) 투자자이므로, 적당한 리스크로 상당한 수익을 얻을 수 있는 주식에 관심이 많습니다.",
        "사용자는 고위험(공격적) 투자자이므로, 안정적으로 보장된 적은 수익 보다 리스크가 존재해도 높은 수익을 얻을 수 있는 주식에 관심이 많습니다.",
        ]

    report = agent1.run(target=target,
                        company=company,
                        news=news,
                        orderbook=orderbook) #리포트 작성 에이전트
    
    final_answer = agent2.run(target=target,
                              report=report.content,
                              user_persona=user_persona[0]) #최종 답변 작성 에이전트

    print("보고서:", report.content)
    print("\n\n최종 답변:", final_answer['recommendation'])
    if final_answer['recommendation']!="관망":  #관망 나올시 비율 적용 x
        percentage = re.findall(r'\d+%', final_answer['weights'])
        print(f"{final_answer['recommendation']} 비율:",percentage[0])