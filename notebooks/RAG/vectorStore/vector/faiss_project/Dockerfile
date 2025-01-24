# Python 3.9 slim 이미지 사용 (더 작은 크기)
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지 설치 (faiss에 필요한 라이브러리 설치)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# 환경 변수 설정 (UTF-8 설정 및 FastAPI 런타임 환경 설정)
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# 요구사항 파일 복사 및 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 및 데이터 복사 (데이터 폴더가 존재하는 경우만 복사)
COPY src/ ./src/
COPY config.py ./
COPY run.py ./

# data 폴더가 존재하면 복사, 없으면 무시
RUN if [ -d "data" ]; then cp -r data/ ./data/; fi

# 포트 개방
EXPOSE 8060

# FastAPI 서버 실행 (gunicorn + uvicorn 활용)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "run:app", "--bind", "0.0.0.0:8060", "--workers", "4"]
