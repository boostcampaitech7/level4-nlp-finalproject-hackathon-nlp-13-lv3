import os
import sqlite3
import requests
import json
from dotenv import load_dotenv


class KakaoNotification:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        load_dotenv(dotenv_path=env_path)

        self.api_url = os.getenv("KAKAO_API_URL", "https://kapi.kakao.com/v2/api/talk/memo/default/send")
        self.client_id = os.getenv("KAKAO_CLIENT_ID")
        self.client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI")

        self.db_path = os.path.join(base_dir, "tokens.db")
        self._init_db()

    def _init_db(self):
        """ SQLite 데이터베이스 초기화 및 테이블 확인 """
        print("📌 [DEBUG] 데이터베이스 초기화 중...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                position TEXT,
                justification TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()
        conn.close()
        print("✅ [DEBUG] 데이터베이스 초기화 완료.")

    def send_auth_request(self, user_id, trade_id):
        """ 사용자에게 카카오 인증 요청 메시지 전송 (거래 ID 포함) """
        state_param = f"&state={trade_id}" if trade_id else ""
        auth_url = (
            f"https://kauth.kakao.com/oauth/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope=talk_message"
            f"{state_param}"
        )
        print(f"📢 [DEBUG] {user_id}에게 카카오 인증 요청 전송")
        print(f"🔗 [INFO] 인증 URL: {auth_url}")
        return auth_url

    def save_trade_request(self, user_id, position, justification):
        """ 거래 요청을 저장하고 일련번호를 반환 """
        print(f"📌 [DEBUG] 거래 저장 요청 - user_id: {user_id}, position: {position}, justification: {justification}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trade_requests (user_id, position, justification) 
            VALUES (?, ?, ?)
        """, (user_id, position, justification))
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"✅ [DEBUG] 거래 요청 저장 완료 - 거래 ID: {trade_id}")
        return trade_id

    def get_trade_request(self, trade_id):
        """ 거래 요청 정보를 조회 """
        print(f"📌 [DEBUG] 거래 요청 조회 - 거래 ID: {trade_id}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, position, justification FROM trade_requests WHERE id = ?
        """, (trade_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            print(f"✅ [DEBUG] 거래 요청 조회 성공 - 거래 ID: {trade_id}, 데이터: {row}")
        else:
            print(f"⚠️ [WARNING] 거래 ID {trade_id}의 데이터 없음")
        return row

    def get_tokens(self, user_id):
        """ 특정 사용자의 액세스 토큰 및 리프레시 토큰 조회 """
        print(f"📌 [DEBUG] {user_id}의 액세스 토큰 조회 중...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT access_token, refresh_token FROM user_tokens WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            print(f"✅ [DEBUG] {user_id}의 액세스 토큰 조회 성공: {row[0]}")
            return row
        else:
            print(f"⚠️ [WARNING] {user_id}의 액세스 토큰이 없습니다.")
            return None, None  # 토큰이 없으면 None 반환

    def get_access_token(self, user_id, code):
        """ 카카오 OAuth 인증 코드를 사용하여 액세스 토큰을 요청 """
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]

            # DB에 저장
            self.save_tokens(user_id, access_token, refresh_token)

            return access_token
        else:
            print(f"❌ [ERROR] 액세스 토큰 요청 실패: {response.text}")
            return None

    def save_tokens(self, user_id, access_token, refresh_token):
        """ SQLite에 사용자 토큰 저장 """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_tokens (user_id, access_token, refresh_token) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = excluded.refresh_token
        """, (user_id, access_token, refresh_token))
        conn.commit()
        conn.close()
        print(f"✅ [DEBUG] 사용자 {user_id} 토큰 저장 완료")

    def send_trade_request(self, trade_id):
        """ 거래 요청 정보를 불러와 카카오톡 메시지를 전송 """
        trade_data = self.get_trade_request(trade_id)
        if not trade_data:
            return f"❌ 거래 ID {trade_id}의 요청을 찾을 수 없습니다."

        user_id, position, justification = trade_data
        print(f"📌 [DEBUG] 거래 요청 전송 중 - 거래 ID: {trade_id}, user_id: {user_id}")

        access_token, _ = self.get_tokens(user_id)
        print(f"📌 [DEBUG] {user_id}의 액세스 토큰 조회 결과: {access_token}")

        if not access_token:
            print(f"📢 [DEBUG] 액세스 토큰 없음, 인증 요청 실행 - user_id: {user_id}")
            return self.send_auth_request(user_id, trade_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # ✅ template_object를 올바르게 변환
        template_object = {
            "object_type": "text",
            "text": f"📢 거래 요청\n거래 ID: {trade_id}\n포지션: {position}\n근거: {justification}",
            "link": {"web_url": "https://www.example.com"}
        }

        data = {
            "template_object": json.dumps(template_object, ensure_ascii=False)  # ✅ JSON 문자열로 변환
        }

        response = requests.post(self.api_url, headers=headers, data=data)

        if response.status_code == 200:
            print(f"✅ [DEBUG] 거래 요청 전송 성공 - 거래 ID: {trade_id}")
            return f"✅ 거래 ID {trade_id} 요청이 성공적으로 전송되었습니다."
        else:
            print(f"❌ [ERROR] 거래 요청 전송 실패 - 거래 ID: {trade_id}, 응답: {response.text}")
            return f"❌ 거래 ID {trade_id} 요청 실패: {response.text}"

