# fin_news_analysis_agent.py

import os
import time
import feedparser
from urllib.parse import quote
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph의 기본 클래스와 상태 타입 (파일명이 LangGraph_base.py)
from LangGraph_base import Node, GraphState

class GoogleNewsFetcher:
    """
    구글 뉴스 RSS를 이용해 특정 키워드 관련 최신 뉴스를 불러오는 클래스입니다.
    타이틀, URL, 발행일 정보를 추출합니다.
    """
    def __init__(self):
        self.base_url = "https://news.google.com/rss"

    def _fetch_news(self, url: str, k: int = 3) -> list:
        news_data = feedparser.parse(url)
        entries = news_data.entries[:k]
        result = []
        for entry in entries:
            published = entry.get("published", "발행일 정보 없음")
            result.append({
                "title": entry.title,
                "link": entry.link,
                "published": published
            })
        return result

    def _collect_news(self, news_list: list) -> list:
        if not news_list:
            print("해당 키워드의 뉴스가 없습니다.")
            return []
        result = []
        for news in news_list:
            result.append({
                "title": news["title"],
                "url": news["link"],
                "published": news["published"]
            })
        return result

    def fetch_news_by_keyword(self, keyword: str, k: int = 3) -> list:
        if keyword:
            encoded_keyword = quote(keyword)
            url = f"{self.base_url}/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = f"{self.base_url}?hl=ko&gl=KR&ceid=KR:ko"
        news_list = self._fetch_news(url, k)
        return self._collect_news(news_list)

class NewsAnalysisAgent(Node):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()  # 환경변수 로드

        # LLM 초기화 
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.5
        )

        # 시스템 프롬프트: 뉴스 분석 전문가 역할 정의
        self.system_prompt = SystemMessage(content=(
            "당신은 주식 투자 관련 뉴스를 분석하는 전문가입니다. 다음 규칙을 따르세요:\n"
            "1. 특정 기업과 관련된 최신 뉴스 기사의 타이틀, URL, 발행일 정보를 확인하세요.\n"
            "2. 뉴스 발행일을 기준으로 최신 뉴스와 과거 뉴스 간의 트렌드 변화 및 시사점을 분석하세요.\n"
            "3. 뉴스 기사에 포함된 주요 이슈(사업 확장, 경영 이슈, 시장 반응 등)를 파악하여, 해당 종목의 주식시장에 미치는 영향을 평가하세요.\n"
            "4. 긍정적 및 부정적 시그널, 투자 리스크와 기회 요인을 명확하게 서술하세요.\n"
            "5. 최종 분석 결과는 뉴스 정보 원본(타이틀, 발행일, UR)과 매매의견과 투자 근거를 포함하여 논리적으로 작성해야 합니다."
        ))

        # 최종 프롬프트 템플릿: 뉴스 데이터(타이틀, 발행일, URL)를 기반으로 분석 요청
        self.final_prompt_template = PromptTemplate.from_template(
            "아래의 뉴스 데이터를 기반으로, 해당 기업의 주식에 미치는 영향과\n"
            "투자 전략을 평가하세요.\n\n"
            "참고한 뉴스 데이터 (타이틀, 발행일, URL):\n{news_data}\n\n"
            "발행일을 참고하여 참고한 뉴스 발행일 기간을 명시하세요."
            "분석 요청:\n{query}\n\n"
            "분석 결과를 다음 형식으로 작성하세요:\n"
            "뉴스 데이터:\n"
            "매매의견:\n"
            "투자 근거:"
        )

        # LLM 체인 구성 (프롬프트 템플릿과 LLM 모델 연결)
        self.final_answer_chain = self.final_prompt_template | self.llm

        # 뉴스 데이터를 불러오기 위한 인스턴스 생성
        self.news_fetcher = GoogleNewsFetcher()

    def format_news_data(self, news_items: list) -> str:
        """
        불러온 뉴스 데이터를 타이틀, URL, 발행일 정보를 포함하는 문자열로 포맷합니다.
        """
        if not news_items:
            return "뉴스 데이터가 없습니다."
        formatted = ""
        for idx, news in enumerate(news_items, start=1):
            formatted += (f"{idx}. {news['title']} (발행일: {news['published']})\n"
                          f"   URL: {news['url']}\n")
        return formatted

    def process(self, state: GraphState) -> GraphState:
        print(f"[{self.name}] process() 호출")
        # state에서 'company_name'을 뉴스 검색 키워드로 사용
        company = state.get("company_name", "Unknown")
        # 특정 기업 관련 최신 뉴스 10개를 불러옴
        news_items = self.news_fetcher.fetch_news_by_keyword(company, k=10)
        formatted_news = self.format_news_data(news_items)
        state["news_report"] = formatted_news  # 뉴스 원시 데이터 저장

        # LLM을 통한 뉴스 분석 실행
        query = f"해당 뉴스 데이터가 {company} 주식 시장에 미치는 영향과 투자 전략에 대해 분석해주세요."
        final_answer = self.final_answer_chain.invoke({
            "news_data": formatted_news,
            "query": query
        })
        state["news_analysis"] = final_answer.content

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    agent = NewsAnalysisAgent("NewsAnalysisAgent")
    test_query = "해당 기업의 뉴스가 주식시장에 미치는 영향 분석"
    initial_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(initial_state)
    print("\n=== 뉴스 분석 결과 ===")
    print(final_state.get("news_analysis", "결과 없음"))
