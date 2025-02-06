import os
import requests
from dotenv import load_dotenv

class KakaoNotification:
    def __init__(self):
        load_dotenv()
        self.api_url = os.getenv("KAKAO_API_URL")
        self.client_id = os.getenv("KAKAO_CLIENT_ID")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
        self.user_tokens = {}  # 사용자별 토큰 저장소

    def send_auth_request(self, user_id):
        """
        사용자에게 카카오 인증 요청 메시지 전송
        """
        auth_url = (
            f"https://kauth.kakao.com/oauth/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
        )
        message = f"📢 {user_id}, 아래 링크를 클릭하여 카카오 인증을 진행하세요:\n{auth_url}"
        print(message)  # 실제로는 카카오톡 메시지 전송 로직 추가 가능
        return auth_url

    def get_access_token(self, authorization_code):
        """
        액세스 토큰 발급 요청
        """
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": authorization_code
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token"), token_data.get("refresh_token")
        else:
            print("❌ 액세스 토큰 발급 실패:", response.text)
            return None, None

    def send_message(self, user_id, message):
        """
        카카오톡 메시지 전송 (토큰이 없으면 인증 요청)
        """
        if user_id not in self.user_tokens:
            print(f"✅ {user_id}에 대한 액세스 토큰이 없습니다. 인증 요청을 보냅니다.")
            auth_link = self.send_auth_request(user_id)
            return f"🔗 인증 링크를 보냈습니다: {auth_link}"

        access_token = self.user_tokens[user_id]["access_token"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "template_object": {
                "object_type": "text",
                "text": message,
                "link": {"web_url": "https://example.com"},
                "button_title": "확인"
            }
        }

        response = requests.post(self.api_url, headers=headers, json=data)
        if response.status_code == 401:
            print(f"⚠️ {user_id}의 토큰이 만료되었습니다. 토큰 갱신이 필요합니다.")
            return self.send_auth_request(user_id)
        elif response.status_code == 200:
            return f"✅ {user_id}에게 메시지를 성공적으로 보냈습니다."
        else:
            return f"❌ {user_id}의 메시지 전송 실패: {response.text}"
