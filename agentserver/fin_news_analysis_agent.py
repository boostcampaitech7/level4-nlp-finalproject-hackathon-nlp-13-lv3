import os
import time
import feedparser
from urllib.parse import quote
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph_base에서 Node, GraphState import (파일명이 LangGraph_base.py)
from LangGraph_base import Node, GraphState

class GoogleNewsFetcher:
    """
    기업이나 산업에 대한 뉴스는 주가에 즉각적인 영향을 미치는 핵심 요소입니다.
    실적 발표, 신제품 출시, 대규모 계약 체결, 경영진 변경 등의 뉴스는 
    기업 가치 평가에 중요한 정성적 정보를 제공합니다. 특히 최신 뉴스의 
    감성 분석(긍정/부정)은 단기적 주가 움직임을 예측하는 데 도움이 됩니다.

    이 에이전트는 Google News RSS를 사용하여 키워드 기반의 뉴스 검색을 수행하고,
    각 뉴스 항목의 제목, URL, 발행일 정보를 추출합니다. 수집된 뉴스는 
    LLM을 통해 분석되어 투자 의사결정에 필요한 핵심 인사이트를 제공합니다.

    Attributes:
        base_url (str): 구글 뉴스 RSS 기본 URL
    """
    def __init__(self):
        self.base_url = "https://news.google.com/rss"

    def _fetch_news(self, url: str, k: int = 3) -> list:
        """
        RSS 피드에서 지정된 수의 뉴스 항목을 가져옵니다.

        Args:
            url (str): RSS 피드 URL
            k (int, optional): 가져올 뉴스 항목 수. 기본값은 3

        Returns:
            list: 뉴스 항목 리스트
                각 항목은 딕셔너리 형태:
                {
                    'title': str,
                    'link': str,
                    'published': str
                }
        """
        
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
        """
        뉴스 리스트를 정제된 형식으로 변환합니다.

        Args:
            news_list (list): _fetch_news()로부터 받은 뉴스 항목 리스트

        Returns:
            list: 정제된 뉴스 항목 리스트
                각 항목은 딕셔너리 형태:
                {
                    'title': str,
                    'url': str,
                    'published': str
                }
        """
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
        """
        특정 키워드에 대한 뉴스를 검색하고 수집합니다.

        Args:
            keyword (str): 검색할 키워드
            k (int, optional): 가져올 뉴스 항목 수. 기본값은 3

        Returns:
            list: 수집된 뉴스 항목 리스트
                각 항목은 딕셔너리 형태:
                {
                    'title': str,
                    'url': str,
                    'published': str
                }
        """
        
        if keyword:
            encoded_keyword = quote(keyword)
            url = f"{self.base_url}/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = f"{self.base_url}?hl=ko&gl=KR&ceid=KR:ko"
        news_list = self._fetch_news(url, k)
        return self._collect_news(news_list)

class NewsAnalysisAgent(Node):
    """
    뉴스 데이터를 수집하고 분석하여 투자 인사이트를 제공하는 에이전트입니다.

    Google News에서 특정 기업 관련 뉴스를 수집하고, LLM을 사용하여
    뉴스가 해당 기업의 주가에 미칠 수 있는 영향을 분석합니다.

    Attributes:
        name (str): 에이전트의 이름
        llm (ChatOpenAI): 뉴스 분석에 사용되는 LLM 모델 (gpt-4o-mini)
        system_prompt (SystemMessage): LLM에 제공되는 시스템 프롬프트
        final_prompt_template (PromptTemplate): 뉴스 분석을 위한 프롬프트 템플릿
        final_answer_chain: 프롬프트와 LLM을 연결한 체인
        news_fetcher (GoogleNewsFetcher): 뉴스 수집을 위한 인스턴스
    """
    
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
            "1. 특정 기업과 관련된 최신 뉴스 기사의 타이틀과 발행일 정보를 확인하세요.\n"
            "2. 뉴스 발행일을 기준으로 최신 뉴스와 과거 뉴스 간의 트렌드 변화 및 시사점을 분석하세요.\n"
            "3. 뉴스 기사에 포함된 주요 이슈(사업 확장, 경영 이슈, 시장 반응 등)를 파악하여, 해당 종목의 주식시장에 미치는 영향을 평가하세요.\n"
            "4. 긍정적 및 부정적 시그널, 투자 리스크와 기회 요인을 명확하게 서술하세요.\n"
            "5. 최종 분석 결과는 뉴스 정보 원본(타이틀, 발행일)을 포함하여 논리적으로 작성해야 합니다."
        ))

        # 최종 프롬프트 템플릿: 뉴스 데이터(타이틀, 발행일, URL)를 기반으로 분석 요청
        self.final_prompt_template = PromptTemplate.from_template(
            "아래의 뉴스 데이터를 기반으로, 해당 기업의 주식에 미치는 영향과\n"
            "투자 전략을 평가하세요.\n\n"
            "참고한 뉴스 데이터 (타이틀, 발행일):\n{news_data}\n\n"
            "발행일을 참고하여 뉴스 발행일 기간을 명시하세요.\n\n"
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
        수집된 뉴스 데이터를 분석에 적합한 형식의 문자열로 변환합니다.

        Args:
            news_items (list): 뉴스 항목 리스트
                각 항목은 딕셔너리 형태:
                {
                    'title': str,
                    'url': str,
                    'published': str
                }

        Returns:
            str: 포맷팅된 뉴스 데이터 문자열
                형식:
                1. 뉴스 제목 (발행일: YYYY-MM-DD)
                2. 뉴스 제목 (발행일: YYYY-MM-DD)
                ...
        """

        if not news_items:
            return "뉴스 데이터가 없습니다."
        formatted = ""
        for idx, news in enumerate(news_items, start=1):
            formatted += f"{idx}. {news['title']} (발행일: {news['published']})\n"
        return formatted

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드로서 뉴스 수집 및 분석을 수행합니다.

        Args:
            state (GraphState): 현재 그래프의 상태
                필요한 키:
                - company_name: 분석할 기업명

        Returns:
            GraphState: 업데이트된 상태
                추가되는 키:
                - news_report: 뉴스 분석 결과
                    포함 내용:
                    - 뉴스 데이터 요약
                    - 매매 의견
                    - 투자 근거

        Note:
            최신 뉴스 10개를 수집하여 분석합니다.
        """
        
        print(f"[{self.name}] process() 호출")
        
        # state에서 'company_name'을 뉴스 검색 키워드로 사용
        company = state.get("company_name", "Unknown")
        
        # 특정 기업 관련 최신 뉴스 10개를 불러옴
        news_items = self.news_fetcher.fetch_news_by_keyword(company, k=10)
        formatted_news = self.format_news_data(news_items)
        
        # LLM을 통한 뉴스 분석 실행
        query = f"해당 뉴스 데이터가 {company} 주식 시장에 미치는 영향과 투자 전략에 대해 분석해주세요."
        final_answer = self.final_answer_chain.invoke({
            "news_data": formatted_news,
            "query": query
        })
        state["news_report"] = final_answer.content

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    agent = NewsAnalysisAgent("NewsAnalysisAgent")
    initial_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(initial_state)
    print("\n=== 뉴스 분석 결과 ===")
    print(final_state.get("news_report", "결과 없음"))
