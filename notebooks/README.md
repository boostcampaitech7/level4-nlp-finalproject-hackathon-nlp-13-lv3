# RAG (Retrieval-Augmented Generation) System

## Overview
PDF 문서 파싱부터 임베딩, 검색, 평가까지 RAG 전체 파이프라인 실험한 결과를 포함합니다.

## Project Structure

### 1. 데이터 전처리 (`data_preprocessing/`)
- 원본 데이터 정제 및 전처리 과정
- `data_preprocessing.ipynb`: 초기 전처리 로직
- `data_preprocessing_ver2.ipynb`: 개선된 전처리 로직

### 2. PDF 처리 (`parser+splitter/`)
- PDF 문서 파싱 및 청킹 로직
- 구조화된 텍스트 추출
- PDF 파일 관리
```bash
poetry install  # 의존성 설치
python process_pdf.py  # PDF 처리 실행
```

### 3. 임베딩 서버 (`embedding/`)
- ../embeddingserver 에 통합

### 4. 벡터 저장소 (`vectorStore/`)
- 임베딩 벡터 저장 및 관리
- 그래프 기반 데이터 구조
- 벡터 검색 최적화

### 5. 테스트 및 평가 (`test/`, `g_eval/`)
- MRC(Machine Reading Comprehension) 테스트
- 테스트 데이터셋 생성 및 관리
- G-Eval 기반 성능 평가
- 리포트 데이터셋 수정 및 검증

### 6. 최종 배포 (`final/`)
- 프로덕션 준비 완료된 RAG API
- Gradio 기반 데모 인터페이스
- 실행 스크립트 및 설정

### 7. 웹 애플리케이션 (`app/`)
- FastAPI 기반 백엔드
- Streamlit 프로토타입
- 데이터베이스 연동
- 로깅 및 모니터링

## Installation & Setup

1. 환경 설정:
```bash
# PDF 처리 모듈
cd parser+splitter
poetry install

# 웹 애플리케이션
cd ../app
pip install -r requirements.txt
```

2. 서버 실행:
```bash
# 임베딩 서버
cd embedding
python -m app.main

# API 서버
cd ../final
./eval_server_run.sh

# 웹 애플리케이션
cd ../app
./run.sh
```

## Development Process

1. **데이터 준비**
   - PDF 문서 수집
   - 전처리 및 정제
   - 청킹 전략 최적화

2. **임베딩 & 저장**
   - 텍스트 임베딩 생성
   - 벡터 저장소 구축
   - 검색 성능 최적화

3. **테스트 & 평가**
   - 테스트 데이터셋 구축
   - MRC 성능 평가
   - G-Eval 기반 품질 평가

4. **배포 & 모니터링**
   - API 서버 배포
   - 성능 모니터링
   - 로그 분석

## Evaluation

### MRC 평가
- 정확도, 재현율, F1 스코어
- 응답 시간 및 리소스 사용량
- 상세 내용은 `test/README.md` 참조

### G-Eval 평가
- 응답 품질 평가
- 일관성 검증
- 상세 내용은 `g_eval/` 노트북 참조

## Production Deployment

프로덕션 환경 설정 및 실행:
```bash
cd final
./eval_server_run.sh
```

## Monitoring & Logging

- 접근 로그: `app/logs/access.log`
- 에러 로그: `app/logs/error.log`
- 성능 메트릭스: Prometheus/Grafana 연동