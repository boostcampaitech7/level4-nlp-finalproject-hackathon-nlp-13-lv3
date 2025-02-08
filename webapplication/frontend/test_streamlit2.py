import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# ------------------------------
# 전역 변수 및 함수 정의
# ------------------------------

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


def common_sidebar():
    st.sidebar.markdown("# AI 에이전트를 활용한 주식 매매 시스템")
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

# ------------------------------
# 페이지 함수 정의
# ------------------------------

# 1. 로그인 페이지 (사이드바 없음)


def login_page():
    st.title("nlp13조에 오신걸 환영합니다")
    st.subheader("Please Login")
    if st.button("Login"):
        st.session_state.logged_in = True
        # 로그인 시 기본 페이지를 Dashboard로 설정
        st.session_state.page = "dashboard"
        # 초기 보고서 저장용 DataFrame 생성 (만약 아직 없으면)
        if 'reports' not in st.session_state:
            st.session_state.reports = pd.DataFrame(
                columns=['Date', 'Company', 'Investor Type', 'Report']
            )
        st.rerun()

# 2. Dashboard (보고서 열람) 페이지


def dashboard_page():
    st.title("Dashboard - 보고서 열람")
    # 만약 보고서가 없으면 안내 메시지
    if st.session_state.reports.empty:
        st.info("생성된 보고서가 없습니다.")
    else:
        # 선택된 기업으로 필터링 (선택되지 않았으면 전체 보고서)
        if 'selected_company' in st.session_state:
            filtered_reports = st.session_state.reports[
                st.session_state.reports['Company'] == st.session_state.selected_company
            ]
        else:
            filtered_reports = st.session_state.reports
        if filtered_reports.empty:
            st.info("선택된 기업에 생성된 보고서가 없습니다.")
        else:
            st.dataframe(
                filtered_reports[['Date', 'Company', 'Investor Type']])
            selected_date = st.selectbox(
                "열람할 보고서를 선택하세요", filtered_reports['Date'])
            if selected_date:
                report_content = filtered_reports[filtered_reports['Date']
                                                  == selected_date]['Report'].values[0]
                st.text_area("보고서 내용", report_content, height=400)
        st.markdown(get_table_download_link(
            st.session_state.reports), unsafe_allow_html=True)

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
    total_score = 0
    for question in questions:
        score = st.slider(question, 1, 5, 3, key=question)
        total_score += score
    investor_type = get_investor_type(total_score)
    st.write(f"당신의 투자 성향: **{investor_type}**")
    if st.button("투자 보고서 생성"):
        # 선택된 기업은 사이드바의 선택값 사용
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
        # 보고서 DataFrame에 추가
        st.session_state.reports = pd.concat(
            [st.session_state.reports, new_report], ignore_index=True
        )
        st.session_state.report_generated = report  # 방금 생성한 보고서 저장
        st.session_state.page = "report_view"
        st.rerun()

# 5. 보고서 열람 페이지 (방금 생성한 보고서 보여주기)


def report_view_page():
    st.title("보고서 열람")
    if 'report_generated' in st.session_state:
        st.text_area("생성된 보고서", st.session_state.report_generated, height=400)
    else:
        st.info("생성된 보고서가 없습니다.")
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
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    if not st.session_state.logged_in or st.session_state.page == "login":
        # 로그인 페이지는 사이드바 없이 표시
        login_page()
    else:
        # 로그인 후부터는 공통 사이드바를 표시
        common_sidebar()
        # st.session_state.page에 따라 메인 프레임 콘텐츠 전환
        if st.session_state.page == "dashboard":
            dashboard_page()
        elif st.session_state.page == "create_report":
            create_report_page()
        elif st.session_state.page == "investor_analysis":
            investor_analysis_page()
        elif st.session_state.page == "report_view":
            report_view_page()


if __name__ == "__main__":
    main()
