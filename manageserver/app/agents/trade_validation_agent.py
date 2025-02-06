"""
매매 근거 검증 모듈
- 목업(Mock) 기반으로 매매 근거의 타당성 검증 (실제 OpenAI API 호출 없음)
"""

class TradeValidationAgent:
    def __init__(self, mock_mode=True):
        """
        초기화
        - mock_mode: True일 경우 목업 데이터로 테스트 수행
        """
        self.mock_mode = mock_mode

    def validate(self, position: str, justification: str) -> str:
        """
        매매 근거 검증 수행 (목업 모드)

        Parameters:
        - position (str): 매매 포지션
        - justification (str): 매매 근거

        Returns:
        - str: 검증 결과
        """
        if self.mock_mode:
            # ✅ 목업 데이터 반환 (단순 규칙 기반)
            if "상승세" in justification or "호재" in justification:
                return f"✅ '{position}' 포지션은 타당한 근거입니다. 상승세와 긍정적 호재가 확인되었습니다."
            elif "하락세" in justification or "리스크" in justification:
                return f"❌ '{position}' 포지션은 타당하지 않습니다. 하락세 또는 리스크 요소가 존재합니다."
            else:
                return f"⚠️ '{position}' 포지션의 근거가 불충분합니다. 추가 정보가 필요합니다."
        else:
            # 실제 OpenAI API 호출 (나중에 사용)
            from langchain_openai import ChatOpenAI
            import os
            from dotenv import load_dotenv

            load_dotenv()
            self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
            prompt = f"매매 포지션: {position}\n근거: {justification}\n이 매매가 타당한가요? 분석하세요."
            response = self.llm.invoke(prompt)
            return response
