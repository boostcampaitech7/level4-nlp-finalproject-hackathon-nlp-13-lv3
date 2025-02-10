import os
import time
import asyncio
from typing import Optional
import pandas as pd
from dotenv import load_dotenv

# mojito 설치 필요
import mojito

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

from LangGraph_base import Node, GraphState

load_dotenv()  # .env 파일에서 환경 변수 로드

class DailyChartAnalysisAgent(Node):
    """
    주식의 일봉/월봉 데이터를 수집하고 기술적 분석을 수행하는 에이전트입니다.

    한국투자증권 API를 통해 주가 데이터를 수집하고, LLM을 활용하여
    기술적 분석을 수행하여 투자 전략을 제시합니다.

    Attributes:
        name (str): 에이전트의 이름
        broker (KoreaInvestment): 한국투자증권 API 인터페이스
        chat_model (ChatOpenAI): 기술적 분석에 사용되는 LLM 모델 (gpt-4o-mini)
        target_stocks (dict): 분석 대상 종목들의 코드 매핑
        system_message (SystemMessage): LLM에 제공되는 시스템 프롬프트
        analysis_prompt (PromptTemplate): 기술적 분석을 위한 프롬프트 템플릿
        analysis_chain: 프롬프트와 LLM을 연결한 체인
    """
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.broker = self._initialize_broker()
        
        self.chat_model = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.4,
        )
        
        self.target_stocks = {
            "네이버": "035420",
            "크래프톤": "259960",
            "CJ제일제당": "097950",
            "LG화학": "051910",
            "SK케미칼": "285130",
            "SK하이닉스": "000660",
            "롯데렌탈": "089860",
            "엘앤에프": "066970",
            "카카오뱅크": "323410",
            "한화솔루션": "009830"
        }

        self.system_message = SystemMessage(content=(
            "당신은 주식 가격의 일봉 및 월봉 차트를 분석하여 미래의 가격 변동을 예측하는 기술적 분석 전문가입니다.\n"
            "1. 시장 가격은 모든 정보를 반영한다는 가정 하에서, 수급과 차트 패턴 위주로 분석하세요.\n"
            "2. 이동평균선, 추세선, 캔들 패턴, 거래량 변화, 오실레이터 등을 활용하여 추세와 패턴을 진단하세요.\n"
            "3. 제공된 일봉 데이터와 월봉 데이터를 바탕으로 단기/중기 관점의 미래 가격 움직임을 예측하세요.\n"
            "4. 다우 이론, 엘리엇 파동, 캔들 패턴 등 심화 분석을 이용하여 인사이트를 제공해주세요.\n"
            "5. 매매의견(매수, 매도, 관망)과 구체적인 투자전략(예: 분할매수, 손절라인 설정 등)을 제시하세요."
        ))

        self.analysis_prompt = PromptTemplate(
            template=
            """아래의 주식 데이터를 분석하여 기술적 분석 리포트를 작성해주세요.

            컨텍스트:
            {context}

            질문:
            {question}

            다음 단계로 분석 후 리포트 형태로 뽑아주세요:
            1. 월봉, 일봉 주요 지지선과 저항선 (일봉: 지지선, 저항선, 근거 / 월봉: 지지선, 저항선, 근거)
            2. 전체 거래량 분석 (금일 거래량과 이전 거래량 비교)
            3. 현재 가격, 추천 구매 가격, 추천 손절 가격, 추천 익절 가격 및 그 근거
            4. 주요 기술적 지표 설명 (이동평균선, RSI, MACD 등 및 다우 이론, 엘리엇 파동 등)
            5. 단기, 중기, 장기 전망
            6. 상대적 강도 평가
            7. 최종 투자 결정 (결정 및 이유)
            """,
            input_variables=["context", "question"]
        )

        self.analysis_chain = self.analysis_prompt | self.chat_model

    def _initialize_broker(self) -> Optional[mojito.KoreaInvestment]:
        """
        한국투자증권 API 클라이언트를 초기화합니다.

        환경 변수에서 API 키, 시크릿, 계좌번호를 읽어와 broker 객체를 생성합니다.

        Returns:
            Optional[mojito.KoreaInvestment]: 초기화된 broker 객체
                인증 정보가 없는 경우 None 반환

        Note:
            필요한 환경 변수:
            - KOREAINVESTMENT_KEY
            - KOREAINVESTMENT_SECRET
            - KOREAINVESTMENT_ACC_NO
        """
        
        key = os.getenv('KOREAINVESTMENT_KEY')
        secret = os.getenv('KOREAINVESTMENT_SECRET')
        acc_no = os.getenv('KOREAINVESTMENT_ACC_NO')
        if not all([key, secret, acc_no]):
            print("API 인증 정보가 없습니다. .env 파일을 확인하세요.")
            return None

        return mojito.KoreaInvestment(
            api_key=key,
            api_secret=secret,
            acc_no=acc_no
        )

    def get_daily_data(self, stock_code: str) -> Optional[list]:
        """
        특정 종목의 일봉 데이터를 조회합니다.

        Args:
            stock_code (str): 종목 코드

        Returns:
            Optional[list]: 일봉 데이터 리스트
                각 항목은 딕셔너리 형태로 OHLCV 데이터 포함
                조회 실패 시 None 반환
        """
        
        if not self.broker:
            print("Broker 객체가 없습니다.")
            return None
        try:
            daily_data = self.broker.fetch_ohlcv(
                symbol=stock_code,
                timeframe='D',
                adj_price=True
            )
            return daily_data.get('output2', [])[:-3] if daily_data else None
        except Exception as e:
            print(f"일봉 데이터 조회 실패: {e}")
            return None

    def get_monthly_data(self, stock_code: str) -> Optional[list]:
        """
        특정 종목의 월봉 데이터를 조회합니다.

        Args:
            stock_code (str): 종목 코드

        Returns:
            Optional[list]: 월봉 데이터 리스트
                각 항목은 딕셔너리 형태로 OHLCV 데이터 포함
                조회 실패 시 None 반환
        """
        
        if not self.broker:
            print("Broker 객체가 없습니다.")
            return None
        try:
            monthly_data = self.broker.fetch_ohlcv(
                symbol=stock_code,
                timeframe='M',
                adj_price=True
            )
            return monthly_data.get('output2', [])[:-3] if monthly_data else None
        except Exception as e:
            print(f"월봉 데이터 조회 실패: {e}")
            return None

    def save_to_csv(self, data: list, filename: str) -> Optional[pd.DataFrame]:
        """
        OHLCV 데이터를 DataFrame으로 변환합니다.

        Args:
            data (list): OHLCV 데이터 리스트
            filename (str): 저장할 파일명 (현재는 미사용)

        Returns:
            Optional[pd.DataFrame]: 변환된 DataFrame
                컬럼: date, open, high, low, close, volume
                데이터가 없는 경우 None 반환
        """
        
        if not data:
            return None
        df = pd.DataFrame(data)
        columns = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
        column_names = {
            'stck_bsop_date': 'date',
            'stck_oprc': 'open',
            'stck_hgpr': 'high',
            'stck_lwpr': 'low',
            'stck_clpr': 'close',
            'acml_vol': 'volume'
        }
        df = df[columns].rename(columns=column_names)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def create_context(self, daily_df: pd.DataFrame, monthly_df: pd.DataFrame, company_name: str) -> str:
        """
        일봉과 월봉 데이터를 분석용 문자열 컨텍스트로 변환합니다.

        Args:
            daily_df (pd.DataFrame): 일봉 데이터
            monthly_df (pd.DataFrame): 월봉 데이터
            company_name (str): 기업명

        Returns:
            str: 포맷팅된 분석 컨텍스트
                포함 정보:
                - 회사명
                - 일봉 데이터 범위 및 상세 정보
                - 월봉 데이터 범위 및 상세 정보
        """
        
        context = f"회사명: {company_name}\n\n" \
                  f"[일봉 데이터]\n" \
                  f"제공하는 데이터 날짜: {daily_df['date'].min()} ~ {daily_df['date'].max()}\n" \
                  f"{daily_df.to_string(index=False)}\n\n" \
                  f"[월봉 데이터]\n" \
                  f"제공하는 데이터 날짜: {monthly_df['date'].min()} ~ {monthly_df['date'].max()}\n" \
                  f"{monthly_df.to_string(index=False)}"
        return context

    async def analyze_stock(self, company_name: str, question: str) -> str:
        """
        주식 데이터를 수집하고 기술적 분석을 수행합니다.

        Args:
            company_name (str): 분석할 기업명
            question (str): 분석 요청 질문

        Returns:
            str: 기술적 분석 결과
                포함 내용:
                - 지지선/저항선 분석
                - 거래량 분석
                - 기술적 지표 분석
                - 매매 전략 제안
                
        Note:
            target_stocks에 없는 종목은 분석이 불가능합니다.
        """
        
        if company_name not in self.target_stocks:
            return f"종목 {company_name}은(는) 관심 종목 리스트에 없습니다."

        code = self.target_stocks[company_name]
        print(f"\n=== {company_name}({code}) 분석 시작 ===")

        daily_data = self.get_daily_data(code)
        monthly_data = self.get_monthly_data(code)

        if not daily_data or not monthly_data:
            return "데이터 조회 실패"

        daily_df = self.save_to_csv(daily_data, f"{company_name}_daily.csv")
        monthly_df = self.save_to_csv(monthly_data, f"{company_name}_monthly.csv")

        if daily_df is None or monthly_df is None:
            return "데이터 처리 실패"

        context = self.create_context(daily_df, monthly_df, company_name)
        response = await self.analysis_chain.ainvoke({
            "context": context,
            "question": question
        })
        return response.content

    def run(self, company_name: str, question: str = "차트 분석을 요청합니다.") -> str:
        """
        동기식 실행을 위한 wrapper 함수입니다.

        Args:
            company_name (str): 분석할 기업명
            question (str): 분석 요청 질문

        Returns:
            str: 분석 결과
        """
        
        return asyncio.run(self.analyze_stock(company_name, question))

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드로서 차트 분석을 수행합니다.

        Args:
            state (GraphState): 현재 그래프의 상태
                필요한 키:
                - company_name: 분석할 기업명
                - chart_question (optional): 분석 요청 질문

        Returns:
            GraphState: 업데이트된 상태
                추가되는 키:
                - daily_chart_report: 차트 분석 결과

        Note:
            chart_question이 없을 경우 기본 분석 질문을 사용합니다.
        """
        
        print(f"[{self.name}] process() 호출")
        company = state.get("company_name", "")
        question = state.get("chart_question", "최근 일봉과 월봉 데이터를 기반으로, 주요 지지선과 저항선, 거래량 변화, 기술적 지표(RSI, MACD 등)를 고려하여 단기 및 중기 주가 전망과 추천 매매 전략(매수/매도/관망)을 구체적으로 분석해 주세요.")

        analysis_result = asyncio.run(self.analyze_stock(company, question))
        state["daily_chart_report"] = analysis_result

        time.sleep(0.5)
        return state

if __name__ == "__main__":
    agent = DailyChartAnalysisAgent("DailyChartAnalysisAgent")
    result = agent.run("크래프톤", "현재 차트 추세와 향후 전망을 알려주세요.")
    print("\n분석 결과:")
    print(result)
