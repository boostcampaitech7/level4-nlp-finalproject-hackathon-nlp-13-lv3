import os
import json
import requests
from app.core.database import Database
from app.services.stock_api import StockAPI

class KakaoNotification:
    """ 카카오톡 알림 기능 """

    def __init__(self):
        self.db = Database()
        self.stock_api = StockAPI()
        self.kakao_api_url = os.getenv("KAKAO_API_URL")
        self.kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
        self.kakao_token_url = "https://kauth.kakao.com/oauth/token"
        self.client_id = os.getenv("KAKAO_CLIENT_ID")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI")

    def send_trade_request(self, trade_id):
        """ 거래 요청 정보를 불러와 카카오톡 메시지 전송 (현재 주가 포함) """
        trade_data = self.db.get_trade_request(trade_id)
        print(f"🔍 [DEBUG] trade_data: {trade_data}")  # 🔍 디버깅용

        if not trade_data:
            return f"❌ 거래 ID {trade_id}의 요청을 찾을 수 없습니다."

        user_id, stock_code, position, justification = trade_data
        access_token, _ = self.db.get_tokens(user_id)

        if not access_token:
            # ✅ 액세스 토큰이 없으면 카카오 인증 URL 반환
            auth_url = (
                f"{self.kakao_auth_url}"
                f"?client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}"
                f"&response_type=code"
                f"&state={trade_id}"
            )
            return {
                "error": "❌ 사용자 액세스 토큰 없음",
                "auth_url": auth_url  # ✅ 인증 URL 반환
            }

        current_price = self.stock_api.fetch_stock_price(stock_code)

        template_object = {
            "object_type": "feed",
            "content": {
                "title": "📢 거래 요청",
                "description": f"거래 ID: {trade_id}\n종목 코드: {stock_code}\n포지션: {position}\n근거: {justification}\n현재 가격: {current_price}",
                "image_url": "https://example.com/trade_image.png",
                "link": {"web_url": "https://www.example.com"}
            },
            "buttons": [
                {"title": "수락", "link": {"web_url": "https://www.example.com/accept"}},
                {"title": "거부", "link": {"web_url": f"https://your-api.com/reject"}}
            ]
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"template_object": json.dumps(template_object, ensure_ascii=False)}

        # 🔍 ✅ API 요청 전송 로그 추가
        print(f"🔍 [DEBUG] 카카오톡 API 요청 URL: {self.kakao_api_url}")
        print(f"🔍 [DEBUG] 카카오톡 API 요청 데이터: {data}")
        print(f"🔍 [DEBUG] 카카오톡 API 요청 헤더: {headers}")

        response = requests.post(self.kakao_api_url, headers=headers, data=data)

        # 🔍 ✅ 응답 로그 추가
        print(f"🔍 [DEBUG] 카카오톡 API 응답 코드: {response.status_code}")
        print(f"🔍 [DEBUG] 카카오톡 API 응답 내용: {response.text}")

        if response.status_code == 200:
            return f"✅ 거래 ID {trade_id} 요청이 성공적으로 전송되었습니다."
        return f"❌ 거래 ID {trade_id} 요청 실패: {response.text}"

