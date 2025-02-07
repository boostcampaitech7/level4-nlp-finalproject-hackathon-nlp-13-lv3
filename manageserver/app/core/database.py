import os
import sqlite3


class Database:
    """
    SQLite 데이터베이스를 관리하는 클래스.
    사용자별 액세스 토큰 및 리프레시 토큰을 저장하고 조회할 수 있음.
    """

    def __init__(self):
        """ 데이터베이스 초기화 및 연결 """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "tokens.db")
        self._init_db()

    def _init_db(self):
        """ 데이터베이스 테이블 생성 (없으면 자동 생성) """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_tokens(self, user_id: str, access_token: str, refresh_token: str):
        """
        사용자별 액세스 토큰 및 리프레시 토큰 저장
        - 기존 유저가 있으면 업데이트, 없으면 새로 삽입
        """
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

    def get_tokens(self, user_id: str):
        """
        특정 사용자의 액세스 토큰 및 리프레시 토큰 조회
        - 존재하지 않으면 (None, None) 반환
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT access_token, refresh_token FROM user_tokens WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row if row else (None, None)

    def delete_tokens(self, user_id: str):
        """
        특정 사용자의 토큰 정보 삭제
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def list_all_users(self):
        """
        저장된 모든 사용자 ID 조회 (디버깅용)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM user_tokens")
        users = cursor.fetchall()
        conn.close()
        return [user[0] for user in users]


# ✅ 디버깅 테스트 코드 (직접 실행 시 동작)
if __name__ == "__main__":
    db = Database()
    db.save_tokens("test_user", "sample_access_token", "sample_refresh_token")
    print("토큰 저장 완료!")

    tokens = db.get_tokens("test_user")
    print(f"test_user의 토큰 조회: {tokens}")

    db.delete_tokens("test_user")
    print("test_user 토큰 삭제 완료!")

    print(f"모든 사용자 조회: {db.list_all_users()}")
