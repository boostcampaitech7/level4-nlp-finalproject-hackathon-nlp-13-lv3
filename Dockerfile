# Python 3.9 베이스 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 요구사항 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 및 데이터 복사
COPY src/ ./src/
COPY config.py .
COPY run.py .
COPY data/ ./data/

# FastAPI 서버 실행
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8060"]

# 포트 개방
EXPOSE 8060
