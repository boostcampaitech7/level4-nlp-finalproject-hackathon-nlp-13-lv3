import mojito
import pandas as pd
import openai
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일에서 환경 변수 로드

class MicroeconomicAgent:
    def __init__(self):
        # 기존 코드 유지

        # API 인증 정보 읽기
        koreainvestment_key = os.getenv('KOREAINVESTMENT_KEY')
        koreainvestment_secret = os.getenv('KOREAINVESTMENT_SECRET')
        koreainvestment_acc_no = os.getenv('KOREAINVESTMENT_ACC_NO')

        if not koreainvestment_key or not koreainvestment_secret or not koreainvestment_acc_no:
            print("API 인증 정보가 없습니다. .env 파일을 확인하세요.")
            return

        # broker 객체 생성
        self.broker = mojito.KoreaInvestment(
            api_key=koreainvestment_key,
            api_secret=koreainvestment_secret,
            acc_no=koreainvestment_acc_no
        )
        
        # OpenAI API 키 설정
        openai_api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = openai_api_key
        
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

        # 시스템 프롬프트 설정
        self.system_prompt = "당신은 미시경제 분석 전문가입니다. 주식 가격의 추세와 패턴을 분석하여 미래의 가격 변동을 예측해야 합니다.\n" \
                            "1. 시장 가격은 모든 정보를 반영한다는 전제 하에 분석합니다.\n" \
                            "2. 가격의 움직임은 추세와 패턴을 따릅니다.\n" \
                            "3. 제공된 일봉 데이터와 월봉 데이터를 활용하여 추세와 패턴을 분석합니다.\n" \
                            "4. 다우 이론, 갠 이론, 이동평균선, 추세 분석, 엘리어트 이론 등을 참고하여 분석합니다.\n" \
                            "5. 앞으로의 수요와 공급 변화를 예측하고, 이를 통해 미래 가격을 예측하세요.\n" \
                            "6. 분석 결과는 'YYYY년도 MM월 DD일자 일봉/월봉 분석' 형식으로 날짜와 출처 정보를 포함하세요."

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

    # ... (나머지 코드는 동일)


    def get_daily_data(self, stock_code):
        """일봉 데이터 조회"""
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
        """데이터를 CSV 파일로 저장"""
        if data:
            df = pd.DataFrame(data)
            # 필요한 컬럼만 선택
            columns = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
            df = df[columns]
            # 컬럼명 변경
            column_names = {
                'stck_bsop_date': 'date',
                'stck_oprc': 'open',
                'stck_hgpr': 'high',
                'stck_lwpr': 'low',
                'stck_clpr': 'close',
                'acml_vol': 'volume'
            }
            df = df.rename(columns=column_names)
            # 날짜 형식 변환
            df['date'] = pd.to_datetime(df['date'])
            # CSV 파일로 저장
            # df.to_csv(filename, index=False)
            # print(f"{filename} 저장 완료")
            return df

    def create_context(self, daily_df, monthly_df, company_name):
        """GPT 모델을 위한 컨텍스트 생성"""
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

    async def get_gpt_analysis(self, context, question):
        """GPT-4o-mini 모델을 사용하여 분석 수행"""
        prompt = self.final_prompt_template.format(context=context, question=question)

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # 분석의 다양성을 높이기 위한 설정
                max_tokens=1000,  # 응답 길이 제한
                top_p=0.8,  # 더 집중된 응답을 위한 설정
                presence_penalty=0.1,  # 반복을 줄이기 위한 설정
                frequency_penalty=0.1  # 반복을 줄이기 위한 설정
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT 분석 중 오류 발생: {str(e)}"

    async def analyze_stock(self, company_name, question):
        """종목 분석"""
        if company_name in self.target_stocks:
            code = self.target_stocks[company_name]
            daily_data = self.get_daily_data(code)
            monthly_data = self.get_monthly_data(code)

            print(f"\n=== {company_name}({code}) 분석 결과 ===")
            
            # CSV 파일로 저장 및 DataFrame 반환
            daily_df = self.save_to_csv(daily_data, f"{company_name}_daily.csv")
            monthly_df = self.save_to_csv(monthly_data, f"{company_name}_monthly.csv")

            # GPT 분석을 위한 컨텍스트 생성
            context = self.create_context(daily_df, monthly_df, company_name)

            # GPT 분석 실행
            analysis = await self.get_gpt_analysis(context, question)

            # 중복된 부분 제거
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

if __name__ == "__main__":
    agent = MicroeconomicAgent()
    question = "현재 미시경제 지표들이 한국 주식 시장에 미치는 영향을 분석하고, 이를 바탕으로 한 투자 전략을 제시해주세요."
    company = "네이버"

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
    asyncio.run(agent.analyze_stock(company, question))
