import time
from dotenv import load_dotenv

import yfinance as yf
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.prompts import PromptTemplate

# LangGraph_base에서 Node, GraphState import (에이전트 구조)
from LangGraph_base import Node, GraphState


class FinancialStatementsAnalysisAgent(Node):
    """
    재무제표 분석 에이전트:
    1) 특정 기업명의 재무제표 데이터를 수집/스크래핑/가공
    2) 각 항목(건전성, 수익성, 성장성, 유동성, 활동성 등)으로 분류
    3) LLM에 전달하여 종합 투자 보고서(재무제표 기반)를 생성
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        load_dotenv()

        # LLM 초기화 (모델명, 온도 등 필요 시 조정)
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",  # 실제 사용 시 "gpt-3.5-turbo" 등으로 교체
            temperature=0.2
        )

        # 재무제표 분석 전문가 역할 시스템 프롬프트
        self.system_prompt = SystemMessage(content=(
            "당신은 재무제표를 심층 분석하여 주식 투자 가치를 평가하는 전문가입니다. 다음 규칙을 따르세요:\n"
            "1. 건전성(부채비율 등), 수익성(ROE, ROA 등), 성장성(매출·영업이익 증가율), "
            "유동성(유동비율), 활동성(재고 회전율 등) 지표를 확인하세요.\n"
            "2. 각 지표가 해당 기업의 최근 몇 년(예: 3년) 또는 분기별 추세에서 어떻게 변화했는지 파악하세요.\n"
            "3. 분석 결과는 'YYYY년도 MM월 DD일자 재무제표 분석' 형식으로 날짜와 출처(가상의 증권사 등)를 포함하세요.\n"
            "4. 분석 근거(재무제표 데이터)와 함께 투자 의견(매수/매도/관망)을 제시하세요.\n"
            "5. 향후 리스크 요인과 추가 확인해야 할 항목이 있다면 함께 언급하세요."
        ))

        # 최종 프롬프트 템플릿:
        # 파이썬의 PromptTemplate.from_template를 이용,
        # 재무제표 데이터를 컨텍스트로, 질문(=분석 요청)을 포맷
        self.final_prompt_template = PromptTemplate.from_template(
            "아래는 특정 기업의 최근 재무제표 데이터입니다. "
            "각 항목(건전성, 수익성, 성장성, 유동성, 활동성)으로 요약했으니 분석해주세요.\n\n"
            "재무제표 데이터:\n{fs_data}\n\n"
            "분석 요청:\n{question}\n\n"
            "아래 단계로 분석을 진행하세요:\n"
            "1. 건전성(부채비율 등) 평가\n"
            "2. 수익성(ROE/ROA 등) 및 성장성(매출·영업이익 증가율) 평가\n"
            "3. 유동성(유동비율), 활동성(회전율 등) 평가\n"
            "4. 종합 투자 의견 및 리스크 요인\n\n"
            "분석 결과:"
        )
        self.final_answer_chain = self.final_prompt_template | self.llm

    def fetch_financial_ratios(self, company_name: str):
        """
        특정 한국 기업의 최근 4개년 재무 비율을 계산하여 가져오는 함수.
        모든 비율을 % 단위로 변환하고, 소수점 둘째 자리에서 반올림.
        """
        company_code_list = {
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

        if company_name not in company_code_list:
            return f"'{company_name}'의 종목 코드를 찾을 수 없습니다."

        company_code = company_code_list[company_name]
        ticker_symbol = f"{company_code}.KS"

        try:
            financial_statement = yf.Ticker(ticker_symbol)

            # 최신 4~5개년 데이터 가져오기 (컬럼 수 부족 시 예외 주의)
            balance_sheet = financial_statement.balance_sheet.iloc[:, :5] if not financial_statement.balance_sheet.empty else None
            income_statement = financial_statement.financials.iloc[:, :5] if not financial_statement.financials.empty else None
            cashflow_statement = financial_statement.cashflow.iloc[:, :5] if not financial_statement.cashflow.empty else None

            # 재무 비율 계산을 위한 주요 데이터 필터링
            selected_items = {
                "Total Assets": "총자산",
                "Invested Capital": "투자자본",
                "Stockholders Equity": "자기자본",
                "Net Income": "순이익",
                "Total Revenue": "총매출액",
                "Operating Income": "영업이익",
                "Total Liabilities Net Minority Interest": "총부채",
                "Long Term Debt": "장기부채",
                "Current Assets": "유동자산",
                "Current Liabilities": "유동부채",
                "Cash And Cash Equivalents": "현금 및 현금성 자산",
                "Accounts Receivable": "매출채권",
            }

            # 데이터 존재 여부 확인 후 필터링 (연도별 저장)
            if balance_sheet is not None:
                years = balance_sheet.columns
            else:
                # 다른 statement들에서 컬럼을 가져올 수도 있음
                if income_statement is not None:
                    years = income_statement.columns
                elif cashflow_statement is not None:
                    years = cashflow_statement.columns
                else:
                    return "해당 기업의 재무제표 데이터를 찾을 수 없습니다."

            filtered_data = {year: {} for year in years}

            for key, label in selected_items.items():
                for year in filtered_data.keys():
                    # 단순 if-elif-elif 구조 (실제로 항목에 맞춰 분리하는 게 더 적절)
                    if balance_sheet is not None and key in balance_sheet.index:
                        filtered_data[year][label] = balance_sheet.loc[key, year]
                    elif income_statement is not None and key in income_statement.index:
                        filtered_data[year][label] = income_statement.loc[key, year]
                    elif cashflow_statement is not None and key in cashflow_statement.index:
                        filtered_data[year][label] = cashflow_statement.loc[key, year]
                    else:
                        filtered_data[year][label] = "데이터 없음"

            # 비율 계산 함수 (소수점 둘째 자리 반올림 + % 변환)
            def calc_ratio(numerator, denominator):
                if (numerator != "데이터 없음" and
                        denominator != "데이터 없음" and
                        denominator != 0):
                    return f"{round((numerator / denominator) * 100, 2)}%"
                return "N/A"

            # 연도별 ROI 및 주요 재무 비율 계산
            ratios_by_year = {}
            for year, data in filtered_data.items():
                ratios_by_year[year] = {
                    "총자산": data["총자산"],
                    "총매출액": data["총매출액"],
                    "영업이익": data["영업이익"],
                    "ROI (투자수익률)": calc_ratio(data["순이익"], data["투자자본"]),
                    "부채비율": calc_ratio(data["총부채"], data["총자산"]),
                    "금융부채비율": calc_ratio(data["장기부채"], data["총자산"]),

                    # 실제 이자보상배율은 "영업이익 / 이자비용"이지만 예시 상 "총부채"로 계산
                    "이자보상배율": calc_ratio(data["영업이익"], data["총부채"]),

                    "유동비율": calc_ratio(data["유동자산"], data["유동부채"]),
                    "총자산영업이익률": calc_ratio(data["영업이익"], data["총자산"]),
                    "총자산순이익률": calc_ratio(data["순이익"], data["총자산"]),
                    "자기자본순이익률(ROE)": calc_ratio(data["순이익"], data["자기자본"]),
                    "현금자산비율": calc_ratio(data["현금 및 현금성 자산"], data["총자산"]),
                    "자산회전율": calc_ratio(data["총매출액"], data["총자산"]),
                    "매출채권회전율": calc_ratio(data["총매출액"], data["매출채권"]),
                }

            return ratios_by_year

        except Exception as e:
            return f"데이터 조회 중 오류 발생: {e}"

    def format_financial_statements(self, fs_data: dict) -> str:
        """
        재무 비율(또는 재무제표) 데이터를 문자열로 가공.
        현재 구조는 '연도'별 정보가 key가 되어 있으며,
        그 내부에 각 재무 항목(부채비율, ROE 등)이 담겨 있음.
        """
        formatted = f"기업명: {self.current_company}\n"

        for year, values in fs_data.items():
            formatted += f"\n[연도: {year}]\n"
            for item, val in values.items():
                formatted += f"{item}: {val}\n"

        return formatted

    def process(self, state: GraphState) -> GraphState:
        """
        LangGraph 노드 인터페이스 구현:
        1) state에서 company_name 가져옴
        2) 재무제표 데이터 수집/포맷
        3) LLM 분석 호출
        4) 결과를 state['fin_statements_report'] 등에 저장
        """
        print(f"[{self.name}] process() 호출")

        company = state.get("company_name", "Unknown")
        self.current_company = company  # 문자열 포맷팅에 사용

        # 간단히 'fs_query' 같은 질의키를 사용하거나, 고정된 질문 사용 가능
        question = "위 재무제표를 기반으로 투자 의견을 제시해주세요."

        # 1) 재무제표(또는 비율) 데이터 수집
        fs_data = self.fetch_financial_ratios(company)

        # 데이터가 문자열(에러 메시지)인지 여부 확인
        if isinstance(fs_data, str):
            # 에러 문자열이므로 state에 에러 메시지만 저장
            state["financial_statements_report"] = fs_data
            return state

        # 2) 문자열로 포맷
        formatted_fs = self.format_financial_statements(fs_data)

        # 3) LLM 분석
        final_answer = self.final_answer_chain.invoke({
            "fs_data": formatted_fs,
            "question": question
        })

        # 4) 결과 저장 (예: 'financial_statements_report' 키)
        state["fin_statements_report"] = final_answer.content

        time.sleep(0.5)
        return state


if __name__ == "__main__":
    # standalone 테스트 예시
    agent = FinancialStatementsAnalysisAgent("FinancialStatementsAnalysisAgent")
    test_state: GraphState = {"company_name": "LG화학"}
    final_state = agent.process(test_state)

    print("\n=== 재무제표 분석 결과 ===")
    print(final_state.get("financial_statements_report", "분석 결과 없음"))
