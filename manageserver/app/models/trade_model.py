"""
거래 기록 저장 (SQLite)
- 매매 결과를 데이터베이스에 저장
"""

import sqlite3

conn = sqlite3.connect('trades.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position TEXT,
        justification TEXT,
        validation_result TEXT,
        execution_status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

def save_trade(position, justification, validation_result, execution_status):
    """
    거래 기록 저장

    Parameters:
    - position (str): 매매 포지션
    - justification (str): 매매 근거
    - validation_result (str): 검증 결과
    - execution_status (str): 매매 실행 상태
    """
    cursor.execute('''
        INSERT INTO trades (position, justification, validation_result, execution_status)
        VALUES (?, ?, ?, ?)
    ''', (position, justification, validation_result, execution_status))
    conn.commit()
