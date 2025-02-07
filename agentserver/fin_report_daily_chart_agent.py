# fin_report_daily_chart_agent.py

import mojito
import pandas as pd
import openai
import asyncio
from dotenv import load_dotenv
import os
import time

# LangGraph 노드 인터페이스를 위한 import
from LangGraph_base import Node, GraphState

load_dotenv()  # .env 파일에서 환경 변수 로드

class DailyChartAnalysisAgent(Node):
    """
    기존 MicroeconomicAgent를 변형한 에이전트:
    - Node 상속 (LangGraph와 호환)
    - '차트·기술적 분석 전문가' 페르소나로 프롬프트 수정
    - 나머지 코드는 기존 로직 최대한 유지
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)  # LangGraph Node 인터페이스 준수

        # API 인증 정보 읽기
        koreainvestment_key = os.getenv('KOREAINVESTMENT_KEY')
        koreainvestment_secret = os.getenv('KOREAINVESTMENT_SECRET')
        koreainvestment_acc_no = os.getenv('KOREAINVESTMENT_ACC_NO')

        if not koreainvestment_key or not koreainvestment_secret or not koreainvestment_acc_no:
            print("API 인증 정보가 없습니다. .env 파일을 확인하세요.")
            self.broker = None
        else:
            # broker 객체 생성
            self.broker = mojito.KoreaInvestment(
                api_key=koreainvestment_key,
                api_secret=koreainvestment_secret,
                acc_no=koreainvestment_acc_no
            )
        
        # OpenAI API 키 설정
        openai_api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = openai_api_key
        
        # 관심 종목 리스트 (원본 코드 유지)
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

        # ★ 페르소나(프롬프트) 수정: "차트·기술적 분석 전문가"  
        self.system_prompt = (
            "당신은 주식 가격의 일봉 및 월봉 차트를 분석하여 미래의 가격 변동을 예측하는 기술적 분석 전문가입니다.\n"
            "1. 시장 가격은 모든 정보를 반영한다는 가정 하에서, 수급과 차트 패턴 위주로 분석하세요.\n"
            "2. 이동평균선, 추세선, 캔들 패턴, 거래량 변화, 오실레이터 등을 활용하여 추세와 패턴을 진단하세요.\n"
            "3. 제공된 일봉 데이터와 월봉 데이터를 바탕으로 단기/중기 관점의 미래 가격 움직임을 예측하세요.\n"
            "4. 다우 이론, 엘리엇 파동, 캔들 패턴 분석 등을 적절히 참고하세요.\n"
            "5. 분석 결과는 'YYYY년도 MM월 DD일자 일봉/월봉 분석' 형식으로 날짜와 출처 정보를 포함하세요.\n"
            "6. 최종적으로 매매의견(매수, 매도, 관망)과 구체적인 투자전략(예: 분할매수, 손절라인 설정 등)을 제시하세요."
        )

        # 최종 답변 프롬프트 템플릿 (원본 코드에서 최소한의 변경만)
        self.final_prompt_template = """
        아래의 주식 데이터를 분석하여 기술적 분석 리포트를 작성해주세요.

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
        """

    def get_daily_data(self, stock_code: str):
        """일봉 데이터 조회 (원본 코드 최대한 유지)"""
        if not self.broker:
            print("Broker 객체가 없습니다.")
            return None
        try:
            daily_data = self.broker.fetch_ohlcv(
                symbol=stock_code,
                timeframe='D',
                adj_price=True
            )
            if daily_data and 'output2' in daily_data:
                return daily_data['output2'][:-3]
            return None
        except Exception as e:
            print(f"일봉 데이터 조회 실패: {e}")
            return None

    def get_monthly_data(self, stock_code: str):
        """월봉 데이터 조회 (원본 코드 최대한 유지)"""
        if not self.broker:
            print("Broker 객체가 없습니다.")
            return None
        try:
            monthly_data = self.broker.fetch_ohlcv(
                symbol=stock_code,
                timeframe='M',
                adj_price=True
            )
            if monthly_data and 'output2' in monthly_data:
                return monthly_data['output2'][:-3]
            return None
        except Exception as e:
            print(f"월봉 데이터 조회 실패: {e}")
            return None

    def save_to_csv(self, data, filename: str):
        """데이터를 CSV 파일로 저장 후 DataFrame 반환 (원본 코드 최대한 유지)"""
        if data:
            df = pd.DataFrame(data)
            columns = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
            df = df[columns]
            column_names = {
                'stck_bsop_date': 'date',
                'stck_oprc': 'open',
                'stck_hgpr': 'high',
                'stck_lwpr': 'low',
                'stck_clpr': 'close',
                'acml_vol': 'volume'
            }
            df = df.rename(columns=column_names)
            df['date'] = pd.to_datetime(df['date'])
            return df
        return None

    def create_context(self, daily_df: pd.DataFrame, monthly_df: pd.DataFrame, company_name: str) -> str:
        """GPT 모델을 위한 컨텍스트 생성 (원본 코드 최대한 유지)"""
        context = f"""
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
        return context

    async def get_gpt_analysis(self, context: str, question: str) -> str:
        """
        GPT-4o-mini 모델을 사용하여 분석 수행 (비동기 원본 로직 유지)
        """
        prompt = self.final_prompt_template.format(context=context, question=question)
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000,
                top_p=0.8,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT 분석 중 오류 발생: {str(e)}"

    async def analyze_stock(self, company_name: str, question: str):
        """
        기존 standalone 실행용 메서드
        특정 종목에 대해 일봉/월봉 데이터를 조회하고, GPT 분석을 수행
        """
        if company_name in self.target_stocks:
            code = self.target_stocks[company_name]
            daily_data = self.get_daily_data(code)
            monthly_data = self.get_monthly_data(code)

            print(f"\n=== {company_name}({code}) 분석 결과 ===")

            daily_df = self.save_to_csv(daily_data, f"{company_name}_daily.csv")
            monthly_df = self.save_to_csv(monthly_data, f"{company_name}_monthly.csv")

            if daily_df is None or monthly_df is None:
                print("일봉/월봉 데이터를 가져오지 못했습니다.")
                return

            context = self.create_context(daily_df, monthly_df, company_name)
            analysis = await self.get_gpt_analysis(context, question)

            # 중복된 부분 제거 (원본 코드 유지)
            lines = analysis.split('\n')
            unique_lines = []
            for line in lines:
                if line not in unique_lines:
                    unique_lines.append(line)
            analysis = '\n'.join(unique_lines)

            print("\nGPT 분석 결과:")
            print(analysis)
        else:
            print(f"종목 {company_name}은(는) 관심 종목 리스트에 없습니다.")

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드 인터페이스.
        state에서 'company_name'과 'question'을 가져와 분석 실행 후, 결과를 state에 저장
        """
        print(f"[{self.name}] process() 호출")

        company_name = state.get("company_name", "LG화학")
        question = state.get("question", "차트 데이터 기반 기술적 분석을 요청합니다.")

        # 비동기 함수를 동기적으로 호출
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(self.analyze_stock(company_name, question))

        # 결과는 콘솔로 출력되므로, 여기서는 간단히 메시지만 저장
        state["daily_chart_report"] = f"{company_name} 분석 완료 (결과 콘솔 출력)"
        time.sleep(0.5)
        return state

if __name__ == "__main__":
    # standalone 테스트
    agent = DailyChartAnalysisAgent("DailyChartAnalysisAgent")
    company = "네이버"
    question = "현재 차트 추세와 향후 전망을 알려주세요."

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(agent.analyze_stock(company, question))
