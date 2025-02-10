import os
import json
import requests
from app.core.database import Database
from app.services.stock_api import StockAPI


class KakaoNotification:
    """
    카카오톡을 이용한 거래 요청 알림 기능을 제공하는 클래스

    Attributes:
        db (Database): PostgreSQL 데이터베이스 인스턴스
        stock_api (StockAPI): 주가 조회 API 인스턴스
        kakao_api_url (str): 카카오톡 API URL
        kakao_auth_url (str): 카카오 인증 URL
        kakao_token_url (str): 카카오 토큰 요청 URL
        client_id (str): 카카오 클라이언트 ID (OAuth)
        redirect_uri (str): 카카오 OAuth 인증 후 리디렉트될 URI
    """

    def __init__(self):
        """카카오톡 API 및 데이터베이스 초기화"""
        self.db = Database()
        self.stock_api = StockAPI()
        self.kakao_api_url = os.getenv("KAKAO_API_URL")
        self.kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
        self.kakao_token_url = "https://kauth.kakao.com/oauth/token"
        self.client_id = os.getenv("KAKAO_CLIENT_ID")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI")

    def send_trade_request(self, trade_id: int) -> dict:
        """
        거래 요청 정보를 불러와 카카오톡 메시지를 전송

        Args:
            trade_id (int): 거래 요청 ID

        Returns:
            dict: 전송 결과 (성공 또는 실패 메시지)
        """
        trade_data = self.db.get_trade_request(trade_id)

        if not trade_data:
            return {"error": f"❌ 거래 ID {trade_id}의 요청을 찾을 수 없습니다."}

        user_id, stock_code, position, justification, task_id = trade_data
        access_token, _ = self.db.get_tokens(user_id)

        # 액세스 토큰이 없을 경우, 사용자에게 인증 링크 제공
        if not access_token:
            auth_url = (
                f"{self.kakao_auth_url}"
                f"?client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}"
                f"&response_type=code"
                f"&state={trade_id}"
            )
            return {"error": "❌ 사용자 액세스 토큰 없음", "auth_url": auth_url}

        # 주가 정보 조회
        current_price = self.stock_api.fetch_stock_price(stock_code) or "데이터 없음"

        # 알림 메시지 구성 (길이 제한 고려)
        description_text = (
            f"📌 거래 ID: {trade_id} | "
            f"📌 종목: {stock_code} | "
            f"📌 포지션: {position} | "
            f"💰 가격: {current_price} | "
            f"💡 근거: {justification[:180]}..." if len(justification) > 180 else justification
        )

        template_object = {
            "object_type": "feed",
            "content": {
                "title": "📢 거래 요청",
                "description": description_text,
                "image_url": "https://example.com/trade_image.png",
                "link": {"web_url": "https://www.example.com"}
            },
            "buttons": [
                {"title": "✅ 수락", "link": {"web_url": "https://www.example.com/accept"}},
                {"title": "❌ 거부", "link": {"web_url": "https://your-api.com/reject"}}
            ]
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"template_object": json.dumps(template_object, ensure_ascii=False)}

        response = requests.post(self.kakao_api_url, headers=headers, data=data)

        if response.status_code == 200:
            return {"success": f"✅ 거래 ID {trade_id} 요청이 성공적으로 전송되었습니다."}
        return {"error": f"❌ 거래 ID {trade_id} 요청 실패: {response.text}"}

    def handle_rejection(self, user_id: str, investor_type: str, company_code: str) -> dict:
        """
        사용자가 거래를 거부했을 때 카카오톡 API로 거부 메시지 전송

        Args:
            user_id (str): 사용자 ID
            investor_type (str): 투자자 유형 (예: "저위험 투자자", "고위험 투자자" 등)
            company_code (str): 6자리 기업 코드

        Returns:
            dict: 거부 요청 결과
        """
        access_token, _ = self.db.get_tokens(user_id)

        if not access_token:
            return {"error": "❌ 사용자 액세스 토큰 없음"}

        rejection_message = {
            "object_type": "text",
            "text": f"🚫 [거래 거부 알림]\n투자자 유형: {investor_type}\n기업 코드: {company_code}\n해당 거래가 거부되었습니다."
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"template_object": json.dumps(rejection_message, ensure_ascii=False)}

        response = requests.post(self.kakao_api_url, headers=headers, data=data)

        if response.status_code == 200:
            return {"success": "✅ 거래 거부 메시지가 성공적으로 전송되었습니다."}
        return {"error": f"❌ 거래 거부 요청 실패: {response.text}"}
