import os
import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import streamlit.components.v1 as components
import time
from auth import set_google_login_btn
import request as req
from dotenv import load_dotenv

load_dotenv()
CHATBOT_URL = os.environ['CHATBOT_URL']
# ------------------------------
# 전역 변수 및 함수 정의
# ------------------------------
hide_streamlit_style = """
    <style>
    /* 오른쪽 상단 햄버거 메뉴 숨기기 */
    #MainMenu {visibility: hidden;}
    /* 앱 하단 푸터 숨기기 */
    footer {visibility: hidden;}
    /* 헤더 전체 숨기기 (Deploy 버튼도 포함될 수 있음) */
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 샘플 기업 리스트 (원하는 기업명으로 수정)
companies = ["CJ제일제당", "LG화학", "SK케미칼", "SK하이닉스",
                       "네이버", "롯데렌탈", "엘엔에프", "카카오뱅크", "크래프톤", "한화솔루션"]

# 투자 성향 질문 리스트
questions = [
    "1. 당신의 투자 경험은 어느 정도입니까?",
    "2. 투자 손실에 대한 당신의 태도는 어떻습니까?",
    "3. 당신의 투자 목표는 무엇입니까?",
    "4. 투자 기간은 얼마나 고려하고 계십니까?",
    "5. 현재 당신의 재무 상황은 어떻습니까?",
    "6. 투자 위험에 대한 당신의 태도는 어떻습니까?",
    "7. 당신의 투자 지식 수준은 어느 정도입니까?",
    "8. 경제 상황 변화에 대한 당신의 대응은 어떻습니까?"
]


def get_investor_type(score):
    if 8 <= score <= 16:
        return "저위험(보수적) 투자자"
    elif 17 <= score <= 24:
        return "중위험(중립적) 투자자"
    elif 25 <= score <= 32:
        return "중고위험(적극적) 투자자"
    else:
        return "고위험(공격적) 투자자"


def get_stock_code(stock_name):

    if stock_name == "CJ제일제당":
        return "097950"
    elif stock_name == "LG화학":
        return "051910"
    elif stock_name == "SK케미칼":
        return "285130"
    elif stock_name == "SK하이닉스":
        return "000660"
    elif stock_name == "네이버":
        return "035420"
    elif stock_name == "롯데렌탈":
        return "089860"
    elif stock_name == "엘엔에프":
        return "066970"
    elif stock_name == "카카오뱅크":
        return "323410"
    elif stock_name == "크래프톤":
        return "259960"
    elif stock_name == "한화솔루션":
        return "009830"


def generate_report(company, investor_type):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""
주식 투자 보고서

생성 일시: {now}
대상 기업: {company}
투자자 유형: {investor_type}

1. 기업 개요
{company}는 한국의 대표적인 기업 중 하나로, [기업 설명]

2. 시장 동향
현재 {company}의 주가는 [주가] 원이며, 최근 [기간] 동안 [등락률]의 변동을 보였습니다.

3. 재무 분석
- 매출액: [매출액] 원
- 영업이익: [영업이익] 원
- EPS: [EPS] 원

4. SWOT 분석
강점(Strengths): [강점]
약점(Weaknesses): [약점]
기회(Opportunities): [기회]
위협(Threats): [위협]

5. {investor_type}을 위한 투자 전략
[투자 전략 설명]

6. 리스크 요인
[리스크 요인 설명]

7. 결론
[결론 및 요약]

※ 본 보고서는 투자 참고 자료일 뿐이며, 실제 투자 결정은 본인의 판단에 따라 이루어져야 합니다.
"""
    return report


def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="investment_reports.csv">CSV 파일 다운로드</a>'
    return href

# 공통 사이드바 (로그인 후에만 표시)


def sidebar_chatbot_button():
    helper_chatbot_html = """
    <style>
    /* 페이지 오른쪽 상단에 고정된 컨테이너 */
    .fixed-helper-chatbot {
        position: fixed;
        top: 20px;    /* 화면 상단으로부터의 간격 (원하는 값으로 조절) */
        right: 20px;  /* 화면 오른쪽으로부터의 간격 (원하는 값으로 조절) */
        z-index: 1000;
    }

    /* 버튼 스타일 */
    .fixed-helper-chatbot button {
        background-color: #007BFF;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    </style>
    <div class="fixed-helper-chatbot">
    <a href="{CHATBOT_URL}" target="_blank">
        <button>도우미 챗봇</button>
    </a>
    </div>
    """

    st.markdown(helper_chatbot_html, unsafe_allow_html=True)


def sidebar_top_buttons():
    # 실제 도우미 챗봇 URL로 대체

    combined_html = f"""
    <style>
    /* 오른쪽 상단에 고정된 컨테이너 */
    .fixed-top-right-buttons {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        display: flex;
        gap: 10px;
        align-items: center;
    }}
    /* 공통 버튼 스타일 */
    .button-style {{
        display: inline-block;
        padding: 8px 16px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        text-decoration: none;
        cursor: pointer;
        color: #ffffff !important;

    }}
    /* 로그아웃 버튼 스타일 */
    .logout-btn {{
        background-color: #f44336;
        color: white;
    }}
    /* 도우미 챗봇 버튼 스타일 */
    .chatbot-btn {{
        background-color: #007BFF;
        color: white;
    }}
    </style>
    <div class="fixed-top-right-buttons">
      <a href="?login_status=logout" class="button-style logout-btn">Log Out</a>
      <a href="{CHATBOT_URL}" target="_blank" class="button-style chatbot-btn">도우미 챗봇</a>
    </div>
    """
    st.markdown(combined_html, unsafe_allow_html=True)

    params = st.query_params
    if "login_status" in params and params["login_status"][0].lower() == "logout":
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.query_params.clear()  # 쿼리 파라미터 초기화
        st.session_state.clear()
        st.rerun()


def common_sidebar():
    st.sidebar.markdown("# AI 주식 매매 관리 시스템")
    nav_option = st.sidebar.radio(
        "페이지 선택", ["Dashboard", "Create Report"],
        index=0 if st.session_state.page in ["dashboard"] else 1
    )
    if nav_option == "Dashboard":
        st.session_state.page = "dashboard"
    elif nav_option == "Create Report":
        if st.session_state.page not in ["create_report", "investor_analysis", "report_view"]:
            st.session_state.page = "create_report"

    # 기업 선택 selectbox는 항상 표시
    company = st.sidebar.selectbox(
        "분석할 기업 선택", companies,
        index=0 if 'selected_company' not in st.session_state else companies.index(
            st.session_state.selected_company)
    )
    st.session_state.selected_company = company

    # sidebar_logout_button()
    # sidebar_chatbot_button()
    sidebar_top_buttons()
# ------------------------------
# 페이지 함수 정의
# ------------------------------

# 1. 로그인 페이지 (사이드바 없음)


def login_page():
    st.title("nlp요리사 팀의")
    st.title("AI 주식 매매 관리 시스템")
    st.subheader(" ")
    st.subheader(" ")
    st.subheader("Please Login")
    st.write(set_google_login_btn(), unsafe_allow_html=True)
    # if st.button("Login"):
    #     st.session_state.logged_in = True
    #     st.query_params.login_status = "login"
    #     # 로그인 시 기본 페이지를 Dashboard로 설정
    #     st.session_state.page = "dashboard"
    #     # 초기 보고서 저장용 DataFrame 생성 (만약 아직 없으면)
    #     if 'reports' not in st.session_state:
    #         st.session_state.reports = pd.DataFrame(
    #             columns=['Date', 'Company', 'Investor Type', 'Report']
    #         )
    #     st.rerun()


def sidebar_logout_button():

    # 사이드바 하단에 고정된 로그아웃 버튼 HTML/CSS 주입
    st.sidebar.markdown(
        """
        <style>
        /* 컨테이너는 오른쪽 상단에 고정되고, 좌우 폭은 내용에 맞게 조정 */
        .sidebar-logout-container {
            position: fixed;
            top: 10px;  /* 화면 상단에서 10px 떨어지도록 설정 */
            right: 10px; /* 오른쪽에서 10px 떨어지도록 설정 */
            z-index: 100;
        }
        /* 버튼은 인라인 블록으로 설정하여 내용에 맞게 크기가 결정됨 */
        .sidebar-logout-btn {
            display: inline-block;
            background-color: #f44336;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-align: center;
            font-weight: bold;
            text-decoration: none;
        }
        </style>
        <div class="sidebar-logout-container">
            <a href="?login_status=logout" class="sidebar-logout-btn">Log Out</a>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 쿼리 파라미터에 "logout"이 있으면 세션 상태 초기화 후 로그인 페이지로 전환
    params = st.query_params
    if "login_status" in params and params["login_status"][0].lower() == "logout":
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.query_params.clear()  # 쿼리 파라미터 초기화
        st.session_state.clear()
        st.rerun()

# 2. Dashboard (보고서 열람) 페이지


def dashboard_page():
    st.title("Dashboard - 보고서 열람")
    # 만약 보고서가 없으면 안내 메시지

    selected_company = st.session_state.selected_company if 'selected_company' in st.session_state else companies[
        0]
    stock_code = get_stock_code(selected_company)
    resp = req.get_report_logs(st.query_params.user_id, stock_code)
    print(resp)
    if resp.status_code == 200:
        print("보고서 로그 조회 성공")
        results = resp.json()
        print(resp.json())
        report_logs = results['report_logs']
        st.session_state.reports = pd.DataFrame(report_logs)
        filtered_reports = st.session_state.reports
        if filtered_reports.empty:
            st.info("생성된 보고서가 없습니다.")
        else:
            options = {}
            for _, row in filtered_reports.iterrows():
                display_str = f"{row['created_at']} {row['stock_name']}"
                options[display_str] = row['task_id']

            # selectbox에서 출력 문자열 선택
            selected_display = st.selectbox(
                "열람할 보고서를 선택하세요", list(options.keys()))

            # 선택한 옵션에 해당하는 task_id 가져오기
            selected_task_id = options[selected_display]
            if selected_task_id:
                report_content = filtered_reports[filtered_reports['task_id']
                                                  == selected_task_id]['report_generate'].values[0]
                status = filtered_reports[filtered_reports['task_id']
                                          == selected_task_id]['status'].values[0]

                st.text_area("보고서 내용", report_content if status ==
                             '완료' else f'보고서 생성 중..\n', height=400)
        hoga = req.get_stock_hoga(stock_code)

        if hoga.status_code == 200:
            print("호가 조회 성공")
            hoga_result = hoga.json()
            print(hoga_result)
            converted_list = []

            # {'company': 'CJ제일제당', 'code': '097950', 'timestamp': '160000', 'asks': [{'price': '250500', 'volume': '272'}, {'price': '251000', 'volume': '449'}, {'price': '251500', 'volume': '967'}, {'price': '252000', 'volume': '1449'}, {'price': '252500', 'volume': '944'}, {'price': '253000', 'volume': '1592'}, {'price': '253500', 'volume': '688'}, {'price': '254000', 'volume': '690'}, {'price': '254500', 'volume': '843'}, {'price': '255000', 'volume': '3993'}], 'bids': [{'price': '250000', 'volume': '6'}, {'price': '249500', 'volume': '378'}, {'price': '249000', 'volume': '4004'}, {'price': '248500', 'volume': '571'}, {'price': '248000', 'volume': '1490'}, {'price': '247500', 'volume': '133'}, {'price': '247000', 'volume': '111'}, {'price': '246500', 'volume': '84'}, {'price': '246000', 'volume': '1174'}, {'price': '245500', 'volume': '73'}], 'total_ask': '11887', 'total_bid': '8024'}

            for hoga in zip(hoga_result['asks'], hoga_result['bids']):

                converted_dict = {}
                converted_dict['회사'] = hoga_result['company']
                converted_dict['종목코드'] = hoga_result['code']
                # 160151 형태의 시간을 16:01:51로 변환
                converted_dict['시간'] = hoga_result['timestamp'][:2] + ':' + \
                    hoga_result['timestamp'][2:4] + \
                    ':' + hoga_result['timestamp'][4:]
                converted_dict['매도호가'] = hoga[0]['price']
                converted_dict['매도잔량'] = hoga[0]['volume']
                converted_dict['매수호가'] = hoga[1]['price']
                converted_dict['매수잔량'] = hoga[1]['volume']
                converted_dict['총 매도잔량'] = hoga_result['total_ask']
                converted_dict['총 매수잔량'] = hoga_result['total_bid']
                converted_list.append(converted_dict)

            st.dataframe(converted_list)
        else:
            st.error("호가 조회 실패")
    else:
        print("보고서 로그 조회 실패")
        # st.dataframe(
        #     filtered_reports[['Date', 'Company', 'Investor Type']])
        # selected_date = st.selectbox(
        #     "열람할 보고서를 선택하세요", filtered_reports['created_at'] + ' ' + filtered_reports['stock_name'])
        # if selected_date:
        #     report_content = filtered_reports[filtered_reports['Date']
        #                                       == selected_date]['Report'].values[0]
        #     st.text_area("보고서 내용", report_content, height=400)

    # if st.session_state.reports.empty:
    #     st.info("생성된 보고서가 없습니다.")
    # else:
    #     # 선택된 기업으로 필터링 (선택되지 않았으면 전체 보고서)
    #     if 'selected_company' in st.session_state:
    #         filtered_reports = st.session_state.reports[
    #             st.session_state.reports['Company'] == st.session_state.selected_company
    #         ]
    #     else:
    #         filtered_reports = st.session_state.reports
    #     if filtered_reports.empty:
    #         st.info("선택된 기업에 생성된 보고서가 없습니다.")
    #     else:
    #         st.dataframe(
    #             filtered_reports[['Date', 'Company', 'Investor Type']])
    #         selected_date = st.selectbox(
    #             "열람할 보고서를 선택하세요", filtered_reports['Date'])
    #         if selected_date:
    #             report_content = filtered_reports[filtered_reports['Date']
    #                                               == selected_date]['Report'].values[0]
    #             st.text_area("보고서 내용", report_content, height=400)
    #     st.markdown(get_table_download_link(
    #         st.session_state.reports), unsafe_allow_html=True)

# 3. Create a Report 페이지 (투자 보고서 생성을 위한 첫 화면)


def create_report_page():
    st.title("Create a Report")
    st.write("아래 버튼을 눌러 투자 성향 분석 페이지로 이동합니다.")
    if st.button("Create a Report"):
        st.session_state.page = "investor_analysis"
        st.rerun()

# 4. 투자 성향 분석 페이지


def investor_analysis_page():
    st.title("투자 성향 분석")

    # 각 질문의 옵션 설명을 딕셔너리로 정의
    q1_options = {
        1: "1점: 크게 불안하고, 매도나 손절을 우선 고려한다.",
        2: "2점: 다소 불안하긴 하지만 시장을 지켜본다.",
        3: "3점: 어느 정도 변동은 감수하고, 상황을 조금 더 살핀다.",
        4: "4점: 변동을 기회로 삼아 추가 매수를 검토한다.",
        5: "5점: 변동 자체를 자연스러운 현상으로 여기고 침착하게 대응한다."
    }
    q2_options = {
        1: "1점: 거의 감수할 수 없으며, 원금 보전에 중점을 둔다.",
        2: "2점: 소폭의 손실(약 5~10%)은 감수할 수 있다.",
        3: "3점: 중간 정도의 손실(약 10~20%)은 장기적으로 회복 가능하다고 본다.",
        4: "4점: 상당한 손실(약 20~30%)도 재투자 기회로 본다.",
        5: "5점: 고위험·고수익 추구로 큰 폭의 손실도 감수할 수 있다."
    }
    q3_options = {
        1: "1점: 1년 미만(단기 투자, 현금화가 매우 중요)",
        2: "2점: 1~2년 정도",
        3: "3점: 3~5년 정도",
        4: "4점: 5~10년 정도",
        5: "5점: 10년 이상(매우 장기)"
    }
    q4_options = {
        1: "1점: 거의 없음. 주식 용어 이해도도 낮음.",
        2: "2점: 기본적인 용어는 알지만, 매매 경험은 많지 않음.",
        3: "3점: 주식 매매를 몇 차례 해봤으며, 기본적인 분석 방법을 조금 알음.",
        4: "4점: 다양한 종목과 금융상품(ETF, 펀드 등)을 경험해 봄.",
        5: "5점: 주식뿐 아니라 선물·옵션 등 파생상품까지 적극 운용 경험이 있음."
    }
    q5_options = {
        1: "1점: 손실 가능성. 위험은 최대한 피하고 싶다.",
        2: "2점: 손실이 얼마나 될지 우선 계산해본 후 수익을 살핀다.",
        3: "3점: 위험과 수익을 균형적으로 고려한다.",
        4: "4점: 기대 수익이 충분하다면 어느 정도 위험은 감수한다.",
        5: "5점: 높은 수익률이라면 위험이 크더라도 투자할 의향이 높다."
    }
    q6_options = {
        1: "1점: 전혀 고려하지 않는다. 오히려 전량 매도나 손절을 고민한다.",
        2: "2점: 신중하게 접근하되, 대부분 현금 보유를 선호한다.",
        3: "3점: 일부 금액은 추가 매수할 수 있지만, 큰 규모는 어렵다.",
        4: "4점: 시장을 분석해 보고, 적극적으로 저점 매수를 노린다.",
        5: "5점: 시장 하락 시 대규모 매수를 통해 수익률 극대화를 노린다."
    }
    q7_options = {
        1: "1점: 변동성이 낮고 안정적인 대형 우량주 위주",
        2: "2점: 배당주·채권형ETF 등 비교적 안정성이 높은 자산",
        3: "3점: 우량주와 성장주를 적절히 섞어 분산 투자",
        4: "4점: 높은 성장 잠재력을 가진 중소형주, 테마주 등에 관심이 많음",
        5: "5점: 단기간 급등주, 고위험 섹터 등 공격적인 종목"
    }
    q8_options = {
        1: "1점: 원금 보전 및 소폭의 이자 수준 수익",
        2: "2점: 인플레이션 헤지 정도의 수익",
        3: "3점: 주식 시장 평균 정도의 수익(시장 수익률) 추구",
        4: "4점: 시장 대비 초과 수익(알파) 추구",
        5: "5점: 단기간 수익 극대화, 공격적인 트레이딩 지향"
    }

    # st.form을 사용하여 한 번에 응답받기
    with st.form("investor_analysis_form"):
        q1 = st.radio(
            "Q1. 주식 시장이 단기간에 큰 폭으로 변동할 때, 나의 심리 상태는 어떠한가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q1_options[x],
            index=2
        )
        q2 = st.radio(
            "Q2. 투자 손실이 발생했을 때, 이를 회복하기 위해 감수할 수 있는 손실 수준은 어느 정도인가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q2_options[x],
            index=2
        )
        q3 = st.radio(
            "Q3. 나의 투자 기간(목표로 하는 투자 유지 기간)은 어느 정도인가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q3_options[x],
            index=2
        )
        q4 = st.radio(
            "Q4. 주식 투자 경험 및 금융상품 지식 수준은 어느 정도인가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q4_options[x],
            index=2
        )
        q5 = st.radio(
            "Q5. 투자 결정 시, 손실 가능성과 수익 가능성 중 어느 쪽을 더 먼저 고려하나요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q5_options[x],
            index=2
        )
        q6 = st.radio(
            "Q6. 급격한 시장 하락 시, 추가 자금을 투입하거나 매수를 고려하는 편인가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q6_options[x],
            index=2
        )
        q7 = st.radio(
            "Q7. 종목 선정 시, 주로 어떤 기준을 가장 중시하나요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q7_options[x],
            index=2
        )
        q8 = st.radio(
            "Q8. 본인이 생각하는 투자 목적은 무엇인가요?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: q8_options[x],
            index=2
        )
        submitted = st.form_submit_button("제출")
    placeholder = st.empty()
    placeholder_write = st.empty()
    if submitted:
        total_score = q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8
        investor_type = get_investor_type(total_score)
        placeholder.success(
            f"총 점수: {total_score}점\n\n당신은 **{investor_type}**입니다.")
        # 필요 시 세션 상태에 저장
        st.session_state.investor_total_score = total_score
        st.session_state.investor_type = investor_type
        # "보고서 생성" 버튼을 추가하여, 사용자가 버튼을 누르면 보고서를 생성하고 보고서 열람 페이지로 이동
        st.session_state.form_submitted = True

        # if st.session_state.get("form_submitted", True):
        for i in range(5, 0, -1):
            placeholder_write.write(f"{i}초 후에 보고서 열람 페이지로 전환됩니다.")
            time.sleep(1)
            placeholder_write.empty()

        investor_type = st.session_state.investor_type

        selected_company = st.session_state.selected_company if 'selected_company' in st.session_state else companies[
            0]
        report = generate_report(selected_company, investor_type)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_report = pd.DataFrame({
            'Date': [now],
            'Company': [selected_company],
            'Investor Type': [investor_type],
            'Report': [report]
        })
        # 기존 보고서 DataFrame에 추가
        st.session_state.reports = pd.concat(
            [st.session_state.reports, new_report], ignore_index=True)
        st.session_state.report_generated = report  # 방금 생성한 보고서를 세션에 저장
        st.session_state.page = "report_view"         # 다음 페이지로 전환
        st.session_state.form_submitted = False
        user_id = st.query_params.get("user_id")
        stock_code = get_stock_code(selected_company)

        resp = req.create_report_task(user_id, stock_code,
                                      st.session_state.investor_type)

        print(resp)

        st.session_state.task_id = resp['task_id']

        st.rerun()
        # if st.button("보고서 생성"):
        #     print('clicked')
        #     investor_type = st.session_state.investor_type

        #     selected_company = st.session_state.selected_company if 'selected_company' in st.session_state else companies[
        #         0]
        #     report = generate_report(selected_company, investor_type)
        #     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     new_report = pd.DataFrame({
        #         'Date': [now],
        #         'Company': [selected_company],
        #         'Investor Type': [investor_type],
        #         'Report': [report]
        #     })
        #     # 기존 보고서 DataFrame에 추가
        #     st.session_state.reports = pd.concat(
        #         [st.session_state.reports, new_report], ignore_index=True)
        #     st.session_state.report_generated = report  # 방금 생성한 보고서를 세션에 저장
        #     st.session_state.page = "report_view"         # 다음 페이지로 전환
        #     st.session_state.form_submitted = False
        #     user_id = st.query_params.get("user_id")
        #     stock_code = get_stock_code(selected_company)

        #     resp = req.create_report_task(user_id, stock_code,
        #                                   st.session_state.investor_type)

        #     print(resp)

        #     st.session_state.task_id = resp['task_id']

        #     st.rerun()


# 5. 보고서 열람 페이지 (방금 생성한 보고서 보여주기)

def report_view_page():
    st.title("보고서 열람")
    resp = req.get_report(st.session_state.task_id,
                          st.query_params.get("user_id"))
    if resp['status'] == '완료':
        st.text_area("생성된 보고서", resp['text'], height=500)
    else:
        st.info(f"생성된 보고서가 없습니다. {resp['status_message']}")
        st.text_area("생성된 보고서", '현재 생성된 보고서가 없습니다.', height=500)
        st.write('보고서 생성 중입니다. 잠시만 기다려주세요.')
        st.rerun()

    if st.button("Dashboard로 돌아가기"):
        st.session_state.page = "dashboard"
        st.rerun()

# ------------------------------
# 메인 실행부
# ------------------------------


def main():

    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state or st.query_params.get("login_status") == "logout":
        st.session_state.page = "login"

    if st.query_params.get("login_status") == "login" and st.query_params.get("user_id") is not None:
        st.session_state.logged_in = True
        if st.session_state.page == "login":
            st.session_state.page = "dashboard"
        # 초기 보고서 저장용 DataFrame 생성 (만약 아직 없으면)
        if 'reports' not in st.session_state:
            st.session_state.reports = pd.DataFrame(
                columns=['Date', 'Company', 'Investor Type', 'Report']
            )
    print("main:", st.session_state.page)
    if not st.session_state.logged_in or st.session_state.page == "login":
        # 로그인 페이지는 사이드바 없이 표시
        login_page()
    else:
        # 로그인 후부터는 공통 사이드바를 표시
        common_sidebar()
        # st.session_state.page에 따라 메인 프레임 콘텐츠 전환
        if st.session_state.page == "dashboard":
            st.query_params.page = "dashboard"
            dashboard_page()
        elif st.session_state.page == "create_report":
            st.query_params.page = "create_report"
            create_report_page()
        elif st.session_state.page == "investor_analysis":
            st.query_params.page = "investor_analysis"
            investor_analysis_page()
        elif st.session_state.page == "report_view":
            st.query_params.page = "report_view"
            report_view_page()


if __name__ == "__main__":
    main()
