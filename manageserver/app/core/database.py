import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# ✅ `.env` 파일 자동 탐색 후 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "..", "config", ".env")
load_dotenv(dotenv_path)


class Database:
    """PostgreSQL 데이터베이스 관리"""

    def __init__(self):
        self.conn_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432")  # 기본값 5432 설정
        }

        # 🔍 환경변수 정상 로드 확인 (디버깅)
        print(f"🔍 [DEBUG] DB 설정 확인: {self.conn_params}")

        # ✅ PostgreSQL 연결 테스트
        try:
            conn = self.get_connection()
            if conn is not None:
                print("✅ [INFO] PostgreSQL 연결 성공")
                conn.close()
        except OperationalError as e:
            print(f"❌ [ERROR] PostgreSQL 연결 실패: {e}")
            exit(1)  # 연결 실패 시 프로그램 종료

        self._init_db()

    def get_connection(self):
        """ PostgreSQL DB 연결 반환 (예외 처리 포함) """
        try:
            return psycopg2.connect(**self.conn_params)
        except OperationalError as e:
            print(f"❌ [ERROR] PostgreSQL 연결 실패: {e}")
            return None  # 연결 실패 시 None 반환

    def _init_db(self):
        """DB에 필요한 테이블 생성"""
        conn = self.get_connection()
        if conn is None:
            print("❌ [ERROR] DB 연결 실패로 테이블 생성 불가")
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
                print("✅ [INFO] 테이블 초기화 완료")
        except Exception as e:
            print(f"❌ [ERROR] 테이블 생성 중 오류 발생: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_trade_request(self, user_id, stock_code, position, justification, task_id):
        """거래 요청을 DB에 저장하고 trade_id 반환"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trade_requests (user_id, stock_code, position, justification, task_id, status) 
                    VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id
                """, (user_id, stock_code, position, justification, task_id))

                trade_id = cursor.fetchone()[0]  # 생성된 trade_id 가져오기
                conn.commit()
                print(f"✅ [INFO] 거래 요청 저장 완료 (trade_id: {trade_id})")
                return trade_id
        except Exception as e:
            print(f"❌ [ERROR] 거래 요청 저장 중 오류 발생: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_trade_request(self, trade_id):
        """특정 거래 요청 정보 조회"""
        query = "SELECT user_id, stock_code, position, justification, task_id FROM trade_requests WHERE id = %s"
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cur:
                cur.execute(query, (trade_id,))
                trade_data = cur.fetchone()
                if trade_data:
                    print(f"✅ [INFO] 거래 요청 조회 성공 (trade_id: {trade_id})")
                else:
                    print(f"⚠️ [WARNING] 거래 요청 없음 (trade_id: {trade_id})")
                return trade_data
        except Exception as e:
            print(f"❌ [ERROR] 거래 요청 조회 중 오류 발생: {e}")
            return None
        finally:
            conn.close()

    def get_tokens(self, user_id):
        """특정 사용자의 액세스 토큰 및 리프레시 토큰 조회"""
        conn = self.get_connection()
        if conn is None:
            return None, None

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT access_token, refresh_token FROM user_tokens WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()
                if row:
                    print(f"✅ [INFO] 토큰 조회 성공 (user_id: {user_id})")
                else:
                    print(f"⚠️ [WARNING] 토큰 없음 (user_id: {user_id})")
                return row if row else (None, None)
        except Exception as e:
            print(f"❌ [ERROR] 토큰 조회 중 오류 발생: {e}")
            return None, None
        finally:
            conn.close()

    def save_tokens(self, user_id, access_token, refresh_token):
        """ 사용자의 액세스 토큰 저장 (중복 시 업데이트) """
        conn = self.get_connection()
        if conn is None:
            print("❌ [ERROR] DB 연결 실패로 토큰 저장 불가")
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
                print(f"✅ [INFO] 토큰 저장 완료 (user_id: {user_id}, access_token: {access_token[:10]}..., refresh_token: {refresh_token[:10]}...)")
        except Exception as e:
            print(f"❌ [ERROR] 토큰 저장 중 오류 발생: {e}")
            conn.rollback()
        finally:
            conn.close()
