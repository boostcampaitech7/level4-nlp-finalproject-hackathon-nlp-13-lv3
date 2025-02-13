# Embedding Server

## Overview
텍스트를 벡터로 변환하고 관리하는 FastAPI 기반의 임베딩 서버입니다.

## Project Structure
```
.
├── app/
│   ├── __init__.py      # 패키지 초기화
│   ├── config.py        # 서버 설정 및 환경 변수
│   ├── embedding.py     # 임베딩 관련 핵심 로직
│   ├── logger.py        # 로깅 설정
│   ├── main.py         # FastAPI 애플리케이션
│   ├── routes.py       # API 엔드포인트 정의
│   └── utils.py        # 유틸리티 함수
├── output.py           # 출력 처리
└── requirements.txt    # 프로젝트 의존성
```

## Features
- 텍스트 임베딩 생성 및 관리
- 벡터 저장 및 검색
- RESTful API 인터페이스
- 체계적인 로깅 시스템

## Installation

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
# .env 파일 생성
cp .env.example .env
# 필요한 환경 변수 설정
```

## Usage

서버 실행:
```bash
python -m app.main
```

## API Documentation

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

`app/config.py`에서 다음 설정을 관리합니다:
- 서버 포트
- 로깅 레벨
- 임베딩 모델 설정
- 기타 환경 설정

## Logging

`app/logger.py`를 통해 구조화된 로깅을 제공합니다:
- 요청/응답 로깅
- 에러 추적
- 성능 모니터링