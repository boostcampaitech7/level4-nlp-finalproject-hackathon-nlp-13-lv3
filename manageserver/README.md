# Manager Server

## Overview
서비스 아키텍처에서의 매니저 서버입니다. API 라우팅, 데이터베이스 관리, 외부 서비스 연동 및 작업 스케줄링을 담당합니다.

## Project Structure
```
.
├── app/
│   ├── api/             # API 엔드포인트 정의
│   │   └── routes.py
│   ├── core/           # 핵심 기능 및 설정
│   │   └── database.py  # 데이터베이스 연결 및 설정
│   ├── models/         # 데이터 모델 정의
│   │   └── schemas.py   # Pydantic 모델
│   ├── services/       # 외부 서비스 연동
│   │   ├── kakao_notification.py  # 카카오 알림 서비스
│   │   └── stock_api.py           # 주식 API 서비스
│   └── tasks/          # 백그라운드 작업
│       └── scheduler.py # 작업 스케줄러
├── requirements.txt    # 프로젝트 의존성
└── run.sh             # 서버 실행 스크립트
```

## Features
- RESTful API 엔드포인트 제공
- 데이터베이스 관리 및 연동
- 카카오 알림 서비스 통합
- 주식 API 연동
- 백그라운드 작업 스케줄링

## Installation

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
# - DATABASE_URL
# - KAKAO_API_KEY
# - STOCK_API_KEY
```

## Deployment

서버 실행:
```bash
./run.sh
```

### 서버 설정
- Port: 30820
- Workers: 2
- Timeout: 300초
- 로그 레벨: INFO
- 로그 파일:
  - 접근 로그: `./logs/access.log`
  - 에러 로그: `./logs/error.log`

## API Documentation

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:30820/docs`
- ReDoc: `http://localhost:30820/redoc`

## Services

### 카카오 알림 서비스
- 투자 알림 발송
- 리포트 생성 완료 알림
- 매매 시그널 알림

### 주식 API 서비스
- 실시간 시세 조회
- 거래 데이터 수집
- 시장 정보 조회

## Task Scheduler
- 정기적인 데이터 수집
- 알림 발송 스케줄링
- 시스템 모니터링

## Logging
- 접근 로그와 에러 로그 분리
- 구조화된 로깅 시스템
- 로그 파일 자동 관리