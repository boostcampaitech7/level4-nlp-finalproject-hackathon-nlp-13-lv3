# Web Application

## Overview
전체 시스템의 웹 인터페이스입니다. FastAPI 기반의 백엔드와 Streamlit 기반의 프론트엔드로 구성되어 있습니다.

## Folder Structure
```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API 엔드포인트
│   │   ├── config.py     # 설정 관리
│   │   ├── db/          # 데이터베이스 관련
│   │   ├── logging.py    # 로깅 설정
│   │   ├── main.py      # FastAPI 애플리케이션
│   │   ├── middleware.py # 미들웨어 설정
│   │   ├── nginx/       # Nginx 설정
│   │   ├── schemas/     # 데이터 모델
│   │   └── temp/        # 임시 파일 저장
│   ├── requirements.txt  # 백엔드 의존성
│   └── run.sh           # 백엔드 실행 스크립트
└── frontend/
    ├── auth.py          # 인증 관리
    ├── main.py          # Streamlit 메인 앱
    └── request.py       # API 요청 처리
```

## Setup & Installation

### Backend

1. 의존성 설치:
```bash
cd backend
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
# .env 파일 생성
cp .env.example .env

# 필요한 환경 변수:
# - DATABASE_URL
# - API_KEYS
# 등을 설정
```

3. 서버 실행:
```bash
./run.sh
```

### Frontend

1. Streamlit 앱 실행:
```bash
cd frontend
streamlit run main.py
```

## Features

### Backend API
- RESTful API 엔드포인트
- PostgreSQL 데이터베이스 연동
- Nginx 리버스 프록시
- 구조화된 로깅

### Frontend
- 사용자 인증 및 권한 관리
- 실시간 데이터 시각화
- 투자 분석 리포트 조회
- 직관적인 사용자 인터페이스

## API Documentation

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database

데이터베이스 스키마 및 마이그레이션은 `backend/app/db/` 디렉토리에서 관리됩니다.

## Logging

로그 파일은 다음 위치에 저장됩니다:
- 접근 로그: `backend/logs/access.log`
- 에러 로그: `backend/logs/error.log`

## Security

- API 키 관리

## Deployment

### Backend
```bash
cd backend
./run.sh
```

### Frontend
```bash
cd frontend
streamlit run main.py --server.port 8501
```

## Development

- API 개발: `backend/app/api/` 디렉토리에 라우트 추가
- 스키마 정의: `backend/app/schemas/` 디렉토리에 모델 추가
- 프론트엔드 개발: `frontend/` 디렉토리에서 Streamlit 컴포넌트 추가

