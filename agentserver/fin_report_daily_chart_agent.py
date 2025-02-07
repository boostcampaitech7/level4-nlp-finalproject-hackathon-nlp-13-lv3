import os
import time
import asyncio
from typing import Optional, Dict, Any
import pandas as pd
from dotenv import load_dotenv
# `mojito2` 설치 필요
import mojito

# 최신 권장 방식으로 모듈 임포트
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate


# 환경변수 로드 
# (.env 파일에 OPENAI_API_KEY, 
# KOREAINVESTMENT_KEY, KOREAINVESTMENT_SECRET, KOREAINVESTMENT_ACC_NO를 설정해주세요.
# )
load_dotenv()

class DailyChartAnalysisAgent:
    def __init__(self):
        # API 인증 정보 읽기
        self.broker = self._initialize_broker()
        
        # LangChain ChatOpenAI 초기화
        self.chat_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
        )
        
        # 관심 종목 리스트
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

        # System Message 정의
        self.system_message = SystemMessage(content=(
            "당신은 주식 가격의 일봉 및 월봉 차트를 분석하여 미래의 가격 변동을 예측하는 기술적 분석 전문가입니다.\n"
            "1. 시장 가격은 모든 정보를 반영한다는 가정 하에서, 수급과 차트 패턴 위주로 분석하세요.\n"
            "2. 이동평균선, 추세선, 캔들 패턴, 거래량 변화, 오실레이터 등을 활용하여 추세와 패턴을 진단하세요.\n"
            "3. 제공된 일봉 데이터와 월봉 데이터를 바탕으로 단기/중기 관점의 미래 가격 움직임을 예측하세요.\n"
            "4. 다우 이론, 엘리엇 파동, 캔들 패턴 등 심화 분석을 이용하여 인사이트를 제공해주세요.\n"
            "5. 매매의견(매수, 매도, 관망)과 구체적인 투자전략(예: 분할매수, 손절라인 설정 등)을 제시하세요."
        ))

        # PromptTemplate 정의
        self.analysis_prompt = PromptTemplate(
            template="""
            아래의 주식 데이터를 분석하여 기술적 분석 리포트를 작성해주세요.
            []

            컨텍스트:
            {context}

            질문:
            {question}

            아래 단계를 고려해 분석을 진행하세요:
            1. 추세 분석 (일봉/월봉 추세, 이동평균선, 거래량 등)
            2. 패턴 분석 (캔들 패턴, 지지/저항 등)
            3. 단기 및 중기 전망
            4. 투자자들을 위한 제안 (매매의견, 손절/익절 전략 등)

            분석 결과:
            """,
            input_variables=["context", "question"]
        )

        # RunnableSequence 정의
        self.analysis_chain = self.analysis_prompt | self.chat_model

    def _initialize_broker(self) -> Optional[mojito.KoreaInvestment]:
        """broker 객체 초기화"""
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
        """일봉 데이터 조회"""
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
        """월봉 데이터 조회"""
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
        """데이터를 DataFrame으로 변환"""
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
        """분석 컨텍스트 생성"""
        return f"""
        회사명: {company_name}

        [일봉 데이터 요약]
        기간: {daily_df['date'].min()} ~ {daily_df['date'].max()}
        최근 종가: {daily_df['close'].iloc[-1]}
        최근 5일 종가 추이: {', '.join(map(str, daily_df['close'].tail().tolist()))}
        최근 5일 거래량 추이: {', '.join(map(str, daily_df['volume'].tail().tolist()))}

        [월봉 데이터 요약]
        기간: {monthly_df['date'].min()} ~ {monthly_df['date'].max()}
        최근 월 종가: {monthly_df['close'].iloc[-1]}
        최근 3개월 종가 추이: {', '.join(map(str, monthly_df['close'].tail(3).tolist()))}
        """

    async def analyze_stock(self, company_name: str, question: str) -> str:
        """특정 종목 분석 실행 및 결과 반환"""
        if company_name not in self.target_stocks:
            return f"종목 {company_name}은(는) 관심 종목 리스트에 없습니다."

        code = self.target_stocks[company_name]
        print(f"\n=== {company_name}({code}) 분석 시작 ===")

        # 데이터 수집 및 처리
        daily_data = self.get_daily_data(code)
        monthly_data = self.get_monthly_data(code)

        if not daily_data or not monthly_data:
            return "데이터 조회 실패"

        daily_df = self.save_to_csv(daily_data, f"{company_name}_daily.csv")
        monthly_df = self.save_to_csv(monthly_data, f"{company_name}_monthly.csv")

        if daily_df is None or monthly_df is None:
            return "데이터 처리 실패"

        # 분석 실행
        context = self.create_context(daily_df, monthly_df, company_name)
        response = await self.analysis_chain.ainvoke({
            "context": context,
            "question": question
        })
        
        return response.content

    def run(self, company_name: str, question: str = "차트 데이터 기반 기술적 분석을 요청합니다.") -> str:
        """메인 실행 함수"""
        return asyncio.run(self.analyze_stock(company_name, question))

if __name__ == "__main__":
    # 테스트 실행
    agent = DailyChartAnalysisAgent()
    answer = agent.run("크래프톤", "현재 차트 추세와 향후 전망을 알려주세요.")
    print("\n분석 결과:")
    print(answer)