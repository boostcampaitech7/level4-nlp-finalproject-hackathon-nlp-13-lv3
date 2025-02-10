import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# 샘플 기업 리스트
companies = ["삼성전자", "현대자동차", "네이버", "카카오", "SK하이닉스"]

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
    href = f'<a href="data:file/csv;base64,{b64}" download="investment_reports.csv">Download CSV File</a>'
    return href


def main():
    st.title("주식 투자 보고서 생성기")

    # 사이드바에 기업 선택 옵션 추가
    selected_company = st.sidebar.selectbox("분석할 기업을 선택하세요:", companies)

    # 메인 화면에 투자 성향 질문 표시
    st.header("투자 성향 평가")
    total_score = 0
    for question in questions:
        score = st.slider(question, 1, 5, 3)
        total_score += score

    investor_type = get_investor_type(total_score)
    st.write(f"당신의 투자 성향: {investor_type}")

    if st.button("투자 보고서 생성"):
        report = generate_report(selected_company, investor_type)
        st.text_area("생성된 보고서", report, height=400)

        # 보고서를 DataFrame에 저장
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_report = pd.DataFrame({
            'Date': [now],
            'Company': [selected_company],
            'Investor Type': [investor_type],
            'Report': [report]
        })

        # 기존 보고서가 있으면 불러오고, 없으면 새로 생성
        if 'reports' not in st.session_state:
            st.session_state.reports = pd.DataFrame(
                columns=['Date', 'Company', 'Investor Type', 'Report'])

        st.session_state.reports = pd.concat(
            [st.session_state.reports, new_report], ignore_index=True)

        st.success("보고서가 생성되었습니다!")

    # 저장된 보고서 목록 표시
    if 'reports' in st.session_state and not st.session_state.reports.empty:
        st.header("저장된 보고서 목록")
        st.dataframe(st.session_state.reports[[
                     'Date', 'Company', 'Investor Type']])

        # 선택한 보고서 표시
        selected_report = st.selectbox(
            "열람할 보고서를 선택하세요:", st.session_state.reports['Date'])
        if selected_report:
            report_content = st.session_state.reports[st.session_state.reports['Date']
                                                      == selected_report]['Report'].values[0]
            st.text_area("선택한 보고서", report_content, height=400)

        # 보고서 다운로드 링크
        st.markdown(get_table_download_link(
            st.session_state.reports), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
