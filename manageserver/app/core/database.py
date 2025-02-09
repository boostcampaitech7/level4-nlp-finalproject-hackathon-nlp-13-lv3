import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# ✅ `.env` 파일 경로 명시적으로 지정하여 로드
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
load_dotenv(dotenv_path)

class Database:
    """PostgreSQL 데이터베이스 관리"""
    def __init__(self):
        self.conn_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", 5432)
        }

        # 🔍 환경변수 정상 로드 확인 (디버깅용)
        print(f"🔍 [DEBUG] DB 설정 확인: {self.conn_params}")

        # ✅ PostgreSQL 연결 가능 여부 테스트
        try:
            self.get_connection()
        except OperationalError as e:
            print(f"❌ [ERROR] PostgreSQL 연결 실패: {e}")
            exit(1)  # 오류 발생 시 프로그램 종료

        self._init_db()

    def _init_db(self):
        """ 테이블이 없으면 생성 """
        conn = self.get_connection()
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
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                stock_code TEXT,
                position TEXT,
                justification TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def get_connection(self):
        """ PostgreSQL DB 연결 반환 (예외 처리 포함) """
        try:
            conn = psycopg2.connect(**self.conn_params)
            return conn
        except OperationalError as e:
            print(f"❌ [ERROR] PostgreSQL 연결 실패: {e}")
            return None  # 오류 발생 시 None 반환

    def get_tokens(self, user_id):
        """ 특정 사용자의 액세스 토큰 및 리프레시 토큰 조회 """
        conn = self.get_connection()
        if conn is None:
            return None, None

        cursor = conn.cursor()
        cursor.execute("SELECT access_token, refresh_token FROM user_tokens WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row if row else (None, None)

    def save_tokens(self, user_id, access_token, refresh_token):
        """ 사용자 액세스 토큰 저장 (중복 시 업데이트) """
        conn = self.get_connection()
        if conn is None:
            return

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_tokens (user_id, access_token, refresh_token) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (user_id) DO UPDATE SET 
            access_token = EXCLUDED.access_token, 
            refresh_token = EXCLUDED.refresh_token
        """, (user_id, access_token, refresh_token))
        conn.commit()
        cursor.close()
        conn.close()

    def get_trade_request(self, trade_id):
        """ trade_id를 기준으로 거래 요청 정보 조회 """
        query = "SELECT user_id, stock_code, position, justification FROM trade_requests WHERE id = %s"
        conn = self.get_connection()
        if conn is None:
            return None

        with conn.cursor() as cur:
            cur.execute(query, (trade_id,))
            return cur.fetchone()

    def get_interested_stocks(self):
        """ 관심 종목 목록 조회 """
        query = "SELECT user_id, stock_code FROM interested_stocks"
        conn = self.get_connection()
        if conn is None:
            return []

        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def save_trade_request(self, user_id, stock_code, position, justification):
        """ 거래 요청을 DB에 저장하고 trade_id 반환 """
        conn = self.get_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trade_requests (user_id, stock_code, position, justification, status) 
            VALUES (%s, %s, %s, %s, 'pending') RETURNING id
        """, (user_id, stock_code, position, justification))

        trade_id = cursor.fetchone()[0]  # 생성된 trade_id 가져오기
        conn.commit()
        cursor.close()
        conn.close()

        return trade_id