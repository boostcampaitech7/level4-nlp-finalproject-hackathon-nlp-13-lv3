# fin_macro_index_agent.py

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate
import time
import asyncio

# LangGraph의 Node와 GraphState 타입을 사용
from LangGraph_base import Node, GraphState

class MacroeconomicAnalysisAgent(Node):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()
        
        # LLM 모델 초기화
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.5
        )

        self.system_prompt = SystemMessage(content=(
            "당신은 거시경제 지표를 분석하여 한국 주식 시장에 미치는 영향을 파악하는 전문가입니다. 다음 규칙을 따르세요:\n"
            "1. 환율, 금리, 원자재 가격 등 각 지표 간의 상호 연관성을 분석하세요.\n"
            "2. 현재 지표들의 움직임이 한국 주식 시장에 미치는 영향을 구체적으로 설명하세요.\n"
            "3. 단기/중기적 관점에서 예상되는 시장 움직임과 그 근거를 제시하세요.\n"
            "4. 주요 리스크 요인과 모니터링이 필요한 지표들을 명시하세요.\n"
            "5. 분석을 바탕으로 한 투자 전략 제시 시 구체적인 근거를 함께 제시하세요."
        ))

        self.final_prompt_template = PromptTemplate.from_template(
            "아래의 현재 시장 지표들을 분석하여 한국 시장에 대한 인사이트를 제공해주세요.\n\n"
            "시장 데이터:\n{market_data}\n\n"
            "분석 요청:\n{query}\n\n"
            "다음 단계로 분석을 진행해주세요:\n"
            "1. 주요 지표들의 현재 상황 파악\n"
            "2. 지표들 간의 상호 연관성 분석\n"
            "3. 한국 시장에 미치는 영향 분석\n"
            "4. 주요 리스크 요인 도출\n"
            "5. 투자 전략 제시\n\n"
            "분석 결과:"
        )

        # 최종 프롬프트 체인 구성
        self.final_answer_chain = self.final_prompt_template | self.llm

    def get_market_data(self) -> dict:
        """시장 데이터 수집 함수"""
        urls = {
            'main': "https://m.stock.naver.com/marketindex/home/major/exchange/bond",
            'bond': "https://m.stock.naver.com/marketindex/home/bondAndInterest/bond/USA",
            'energy': "https://m.stock.naver.com/marketindex/home/energy",
            'metals': "https://m.stock.naver.com/marketindex/home/metals",
            'agri': "https://m.stock.naver.com/marketindex/home/agricultural"
        }
        
        try:
            soups = {}
            for key, url in urls.items():
                response = requests.get(url)
                response.raise_for_status()
                soups[key] = BeautifulSoup(response.text, 'html.parser')
            
            market_data = self._parse_market_data(soups)
            return market_data
            
        except requests.RequestException as e:
            print(f"데이터 수집 오류: {e}")
            return {}

    def _parse_market_data(self, soups: dict) -> dict:
        """파싱된 데이터에서 필요한 정보 추출"""
        data = {}
        sections = {
            'main': ['USD/KRW', 'EUR/KRW', 'GOLD', 'WTI'],
            'bond': ['US 10Y', 'KR 10Y', 'JP 10Y', 'DE 10Y'],
            'energy': ['WTI(Energy)', 'Brent', 'Gasoline', 'Heating Oil'],
            'metals': ['International Gold', 'Domestic Gold', 'Silver', 'Copper'],
            'agri': ['Corn', 'Soybean', 'Wheat', 'Pork']
        }
        for section, items in sections.items():
            soup = soups.get(section)
            if not soup:
                continue
            prices = soup.find_all('span', class_='MainListItem_price__5fu6b')
            fluctuations = soup.find_all('span', class_='Fluctuation_fluctuation__4GE2K')
            for idx, item in enumerate(items):
                if idx < len(prices) and idx*2+1 < len(fluctuations):
                    data[item] = {
                        'price': prices[idx].text,
                        'change': fluctuations[idx*2+1].text.strip()
                    }
        return data

    def format_market_data(self, market_data: dict) -> str:
        """시장 데이터를 문자열로 가공"""
        formatted_text = ""
        sections = {
            "환율 및 원자재": ['USD/KRW', 'EUR/KRW', 'GOLD', 'WTI'],
            "국채 금리": ['US 10Y', 'KR 10Y', 'JP 10Y', 'DE 10Y'],
            "에너지": ['WTI(Energy)', 'Brent', 'Gasoline', 'Heating Oil'],
            "금속": ['International Gold', 'Domestic Gold', 'Silver', 'Copper'],
            "농산물": ['Corn', 'Soybean', 'Wheat', 'Pork']
        }
        for section, items in sections.items():
            formatted_text += f"\n[{section}]\n"
            for item in items:
                if item in market_data:
                    info = market_data[item]
                    formatted_text += f"{item}: {info['price']} (변동: {info['change']})\n"
        return formatted_text

    async def analyze_macro(self, query: str) -> str:
        """비동기 분석 실행 함수"""
        market_data = self.get_market_data()
        if not market_data:
            return "시장 데이터를 가져오는데 실패했습니다."
            
        formatted_data = self.format_market_data(market_data)
        final_answer = await self.final_answer_chain.ainvoke({
            "market_data": formatted_data, 
            "query": query
        })
        return final_answer.content

    def run(self, query: str) -> str:
        """동기식 실행을 위한 wrapper 함수"""
        return asyncio.run(self.analyze_macro(query))

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph에서 호출되는 메인 함수.
        state에서 'macro_question'을 받아 분석 후, 결과를 state['macro_report']에 저장
        """
        print(f"[{self.name}] process() 호출")
        
        # query 추출 (없으면 기본값 사용)
        query = state.get(
            "macro_question",
            "현재 거시경제 지표들이 한국 주식 시장에 미치는 영향을 분석하고, 투자 전략을 제시해주세요."
        )

        # 비동기 함수 호출을 동기 방식으로 처리
        analysis_result = asyncio.run(self.analyze_macro(query))

        # 분석 결과를 state에 저장
        state["macro_report"] = analysis_result

        time.sleep(0.5)
        return state


if __name__ == "__main__":
    # standalone 테스트
    agent = MacroeconomicAnalysisAgent("MacroeconomicAnalysisAgent")
    test_query = "현재 거시경제 지표들이 한국 주식 시장에 미치는 영향을 분석하고, 투자 전략을 제시해주세요."
    answer = agent.run(test_query)
    print("\n=== 분석 결과 ===")
    print(answer)