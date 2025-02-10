import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# `.env` 파일 자동 탐색 후 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "..", "config", ".env")
load_dotenv(dotenv_path)


class Database:
    """PostgreSQL 데이터베이스 관리 클래스"""

    def __init__(self):
        """
        데이터베이스 연결 설정 및 테이블 초기화
        """
        self.conn_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432")  # 기본값 5432 설정
        }

        # PostgreSQL 연결 테스트
        try:
            conn = self.get_connection()
            if conn is not None:
                conn.close()
        except OperationalError as e:
            raise RuntimeError(f"PostgreSQL 연결 실패: {e}")

        self._init_db()

    def get_connection(self):
        """
        PostgreSQL 데이터베이스 연결 반환

        Returns:
            psycopg2.connection: DB 연결 객체 (연결 실패 시 None 반환)
        """
        try:
            return psycopg2.connect(**self.conn_params)
        except OperationalError as e:
            return None

    def _init_db(self):
        """
        필요한 테이블을 생성 (없을 경우에만 생성)
        """
        conn = self.get_connection()
        if conn is None:
            return

        try:
            with conn.cursor() as cursor:
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
                        task_id TEXT,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"테이블 생성 중 오류 발생: {e}")
        finally:
            conn.close()

    def save_trade_request(self, user_id: str, stock_code: str, position: str, justification: str, task_id: str) -> int:
        """
        거래 요청을 데이터베이스에 저장하고 거래 ID 반환

        Args:
            user_id (str): 사용자 ID
            stock_code (str): 종목 코드
            position (str): 매수/매도 포지션
            justification (str): 거래 근거
            task_id (str): 작업 ID

        Returns:
            int: 생성된 거래 ID (저장 실패 시 None 반환)
        """
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trade_requests (user_id, stock_code, position, justification, task_id, status) 
                    VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id
                """, (user_id, stock_code, position, justification, task_id))

                trade_id = cursor.fetchone()[0]  # 생성된 trade_id 반환
                conn.commit()
                return trade_id
        except Exception:
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_trade_request(self, trade_id: int):
        """
        특정 거래 요청 정보를 조회

        Args:
            trade_id (int): 거래 ID

        Returns:
            tuple: (user_id, stock_code, position, justification, task_id) (조회 실패 시 None 반환)
        """
        query = "SELECT user_id, stock_code, position, justification, task_id FROM trade_requests WHERE id = %s"
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cur:
                cur.execute(query, (trade_id,))
                return cur.fetchone()
        except Exception:
            return None
        finally:
            conn.close()

    def get_tokens(self, user_id: str):
        """
        특정 사용자의 액세스 토큰 및 리프레시 토큰을 조회

        Args:
            user_id (str): 사용자 ID

        Returns:
            tuple: (access_token, refresh_token) (조회 실패 시 (None, None) 반환)
        """
        conn = self.get_connection()
        if conn is None:
            return None, None

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT access_token, refresh_token FROM user_tokens WHERE user_id = %s", (user_id,))
                return cursor.fetchone() or (None, None)
        except Exception:
            return None, None
        finally:
            conn.close()

    def save_tokens(self, user_id: str, access_token: str, refresh_token: str):
        """
        사용자 액세스 토큰 저장 (기존 데이터가 있으면 업데이트)

        Args:
            user_id (str): 사용자 ID
            access_token (str): 카카오톡 액세스 토큰
            refresh_token (str): 카카오톡 리프레시 토큰
        """
        conn = self.get_connection()
        if conn is None:
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_tokens (user_id, access_token, refresh_token) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (user_id) DO UPDATE SET 
                    access_token = EXCLUDED.access_token, 
                    refresh_token = EXCLUDED.refresh_token
                """, (user_id, access_token, refresh_token))
                conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()
