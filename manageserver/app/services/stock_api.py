import os
import requests
from dotenv import load_dotenv

load_dotenv()

class StockAPI:
    """ 한국투자증권 API를 이용한 주식 데이터 조회 """

    def __init__(self):
        self.api_key = os.getenv("KOREA_INVEST_API_KEY")
        self.api_secret = os.getenv("KOREA_INVEST_API_SECRET")
        self.acc_no = os.getenv("KOREA_INVEST_ACC_NO")
        self.base_url = "https://api.koreainvestment.com/stock"

    def fetch_stock_price(self, stock_code):
        """ 특정 종목의 현재 가격 조회 """
        url = f"{self.base_url}/{stock_code}/price"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("price")
        except requests.RequestException as e:
            print(f"❌ 주가 조회 실패: {e}")
            return None
