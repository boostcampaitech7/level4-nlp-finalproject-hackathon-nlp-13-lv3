# Python 3.11 slim 이미지 사용 (경량화된 Python 환경)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지 설치 (FAISS 및 기타 종속성에 필요한 패키지 설치)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# tail 사용을 위한 coreutils 설치
RUN apt update && apt install -y coreutils

# 환경 변수 설정 (UTF-8 설정 및 FastAPI 런타임 환경 설정)
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# 요구사항 파일 복사 및 패키지 설치
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 및 설정 복사
COPY src/ ./src/
COPY config.py ./config.py
COPY run.py ./run.py


# 포트 개방
EXPOSE 8060

# FastAPI 서버 실행 (gunicorn + uvicorn 활용, 워커 수 최적화)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "run:app", "--bind", "0.0.0.0:8060", "--workers", "2", "--access-logfile", "data/gunicorn.access.log", "--error-logfile", "data/gunicorn.error.log", "--log-level", "DEBUG"]