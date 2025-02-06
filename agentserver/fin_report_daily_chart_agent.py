import mojito
import pandas as pd
import openai
import asyncio
from dotenv import load_dotenv
import os
import time

load_dotenv()  # .env 파일에서 환경 변수 로드

class DailyChartAnalysisAgent:
    def __init__(self, name: str) -> None:
        self.name = name  # Node 인터페이스를 따르기 위한 이름 저장

        # API 인증 정보 읽기
        self.koreainvestment_key = os.getenv('KOREAINVESTMENT_KEY')
        self.koreainvestment_secret = os.getenv('KOREAINVESTMENT_SECRET')
        self.koreainvestment_acc_no = os.getenv('KOREAINVESTMENT_ACC_NO')

        if not self.koreainvestment_key or not self.koreainvestment_secret or not self.koreainvestment_acc_no:
            print("API 인증 정보가 없습니다. .env 파일을 확인하세요.")
            self.broker = None
        else:
            # broker 객체 생성
            self.broker = mojito.KoreaInvestment(
                api_key=self.koreainvestment_key,
                api_secret=self.koreainvestment_secret,
                acc_no=self.koreainvestment_acc_no
            )
        
        # OpenAI API 키 설정
        openai_api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = openai_api_key
        
        # 관심 종목 리스트 (자동 매핑용)
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

        # 시스템 프롬프트 설정 
        self.system_prompt = (
            "당신은 미시경제 분석 전문가입니다. 주식 가격의 추세와 패턴을 분석하여 미래의 가격 변동을 예측해야 합니다.\n"
            "1. 시장 가격은 모든 정보를 반영한다는 전제 하에 분석합니다.\n"
            "2. 가격의 움직임은 추세와 패턴을 따릅니다.\n"
            "3. 제공된 일봉 데이터와 월봉 데이터를 활용하여 추세와 패턴을 분석합니다.\n"
            "4. 다우 이론, 갠 이론, 이동평균선, 추세 분석, 엘리어트 이론 등을 참고하여 분석합니다.\n"
            "5. 앞으로의 수요와 공급 변화를 예측하고, 이를 통해 미래 가격을 예측하세요.\n"
            "6. 분석 결과는 'YYYY년도 MM월 DD일자 일봉/월봉 분석' 형식으로 날짜와 출처 정보를 포함하세요."
        )

        # 최종 답변 프롬프트 템플릿 정의
        self.final_prompt_template = """
        아래의 주식 데이터를 분석하여 기술적 분석 리포트를 작성해주세요.

        컨텍스트:
        {context}

        질문:
        {question}

        다음 단계로 분석을 진행해주세요:
        1. 추세 분석
        2. 패턴 분석
        3. 단기 및 중기 전망
        4. 투자자들을 위한 제안

        분석 결과:
        """

        # LLM 초기화 및 프롬프트 체인 구성 
        self.llm = openai  # 여기서는 openai.ChatCompletion.create()를 직접 호출하는 것으로 가정
        # final_answer_chain은 get_gpt_analysis()에서 직접 사용합니다.

    def get_daily_data(self, stock_code):
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
            if daily_data and 'output2' in daily_data:
                return daily_data['output2'][:-3]  
            return None
        except Exception as e:
            print(f"일봉 데이터 조회 실패: {e}")
            return None

    def get_monthly_data(self, stock_code):
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
            if monthly_data and 'output2' in monthly_data:
                return monthly_data['output2'][:-3]  
            return None
        except Exception as e:
            print(f"월봉 데이터 조회 실패: {e}")
            return None

    def save_to_csv(self, data, filename):
        """데이터를 CSV 파일로 저장 후 DataFrame 반환"""
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

    def create_context(self, daily_df, monthly_df, company_name):
        """GPT 모델을 위한 컨텍스트 생성: 일봉/월봉 데이터 요약"""
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

    def get_gpt_analysis(self, context, question) -> str:
        """
        GPT-4o-mini 모델을 사용하여 분석 수행 (동기식 호출)
        최소한의 변경만 적용 (원본 프롬프트 유지)
        """
        prompt = self.final_prompt_template.format(context=context, question=question)
        try:
            response = openai.ChatCompletion.create(
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

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드 인터페이스에 맞춘 메서드.
        state에서 'company_name'을 사용하여 종목 코드를 결정하고,
        일봉 및 월봉 데이터를 조회한 후, GPT 분석을 실행하여 결과를 state에 저장합니다.
        """
        print(f"[{self.name}] process() 호출")
        company = state.get("company_name", "Unknown")
        # 만약 state에 'stock_code'가 없다면, target_stocks에서 자동 매핑
        stock_code = state.get("stock_code")
        if not stock_code:
            stock_code = self.target_stocks.get(company, None)
            if stock_code is None:
                print(f"{company} 종목 코드를 찾을 수 없습니다.")
                state["daily_chart_report"] = "종목 코드 매핑 실패."
                return state
        
        daily_data = self.get_daily_data(stock_code)
        monthly_data = self.get_monthly_data(stock_code)
        if daily_data is None or monthly_data is None:
            state["daily_chart_report"] = "일봉/월봉 데이터를 가져오는데 실패했습니다."
            return state

        daily_df = self.save_to_csv(daily_data, f"{company}_daily.csv")
        monthly_df = self.save_to_csv(monthly_data, f"{company}_monthly.csv")
        context = self.create_context(daily_df, monthly_df, company)
        question = f"위 차트 데이터를 바탕으로, {company}의 단기 및 중기 주가 추세와 패턴을 분석하고, 투자자에게 도움이 될 매매의견과 투자 전략(자산 배분 포함)을 도출해주세요."
        analysis = self.get_gpt_analysis(context, question)
        state["daily_chart_report"] = analysis
        time.sleep(0.5)
        return state

if __name__ == "__main__":
    from LangGraph_base import GraphState
    # standalone 테스트용
    # target_stocks를 추가한 부분: 초기 state에 'company_name'이 있으면 target_stocks에서 자동 매핑
    agent = DailyChartAnalysisAgent("DailyChartAnalysisAgent")
    # 예시: LG화학의 종목 코드가 target_stocks에 있을 경우 "051910"로 매핑
    initial_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(initial_state)
    print("\n=== 차트 분석 결과 ===")
    print(final_state.get("daily_chart_report", "결과 없음"))
