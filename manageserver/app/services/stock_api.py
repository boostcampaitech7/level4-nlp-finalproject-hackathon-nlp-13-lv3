import os
import requests
from dotenv import load_dotenv

load_dotenv()


class StockAPI:
    """
    한국투자증권 API를 이용한 주식 데이터 조회 클래스

    Attributes:
        api_key (str): API 접근을 위한 키
        api_secret (str): API 인증을 위한 비밀 키
        acc_no (str): 사용자 계좌 번호
        base_url (str): 한국투자증권 API 기본 URL
    """

    def __init__(self):
        """환경 변수에서 API 키 및 설정 값을 로드하여 초기화"""
        self.api_key = os.getenv("KOREA_INVEST_API_KEY")
        self.api_secret = os.getenv("KOREA_INVEST_API_SECRET")
        self.acc_no = os.getenv("KOREA_INVEST_ACC_NO")
        self.base_url = "https://api.koreainvestment.com/stock"

    def fetch_stock_price(self, stock_code: str) -> float:
        """
        특정 종목의 현재 가격을 조회하여 반환

        Args:
            stock_code (str): 조회할 종목 코드

        Returns:
            float: 종목의 현재 가격 (조회 실패 시 None 반환)
        """
        url = f"{self.base_url}/{stock_code}/price"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            data = response.json()

            # 가격 정보가 존재하는지 확인 후 반환
            price = data.get("price")
            if price is not None:
                return float(price)  # 문자열인 경우 float 변환
            else:
                print(f"⚠️ [WARNING] 가격 정보 없음 (stock_code: {stock_code})")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ [ERROR] 주가 조회 실패: {e}")
            return None
