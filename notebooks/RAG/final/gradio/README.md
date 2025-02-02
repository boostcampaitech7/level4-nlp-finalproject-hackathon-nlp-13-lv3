# 증권사 주식 보고서 RAG 시스템 

- 랩큐에서 제공한 PDF 파일을 FAISS 벡터 검색과 Elasticsearch DB를 활용해서 하이브리드 검색 기반의 RAG 시스템을 Gradio로 구현

## 주요 기능

- FAISS 벡터 검색과 Elasticsearch를 결합한 하이브리드 검색
- BAAI/bge-reranker를 이용한 재순위화
- 다중 모달 콘텐츠 근거 제시 (텍스트, 표, 차트, 그림)
- 자동 이미지 처리 및 임시 파일 관리
- 대화형 인터페이스(멀티턴 지원 X)

## 시스템 요구사항

- Poetry ver 2.0.1
- Python 3.11 이상 (3.11.9 권장)
- 환경 변수 설정
- FAISS API 키
- OpenAI API 키

## 사용 방법

1. poetry install

2. `poetry shell`로 가상환경 실행

3. Gradio 인터페이스 실행:
```bash
python gradio_RAG_test.py
```

4. 웹 브라우저에서 인터페이스 접속 (기본: http://localhost:7860)

5. 텍스트 입력 필드에 금융 분석 관련 질문 입력

- 시스템은 다음과 같이 동작합니다.
    - 하이브리드 검색으로 질의 처리
    - 관련 문서 검색
    - 포괄적인 답변 생성
    - 관련 시각 자료 표시 (메타데이터 base64가 있는 경우)

## 프로젝트 구조

```
gradio/
├── gradio_RAG_test.py   # Gradio 실행 파일
├── pyproject.toml       # 프로젝트 의존성 및 메타데이터
├── README.md            # 프로젝트 문서
├── .env                 # 환경 변수 (직접 생성 필요)
└── temp_images/         # 이미지 임시 저장소 (자동 생성)... 중단 시 자동으로 삭제
```

## 주요 컴포넌트

### 1. CustomSentenceTransformerEmbeddings

multilingual-e5-large-instruct 모델을 사용한 문서 및 쿼리 임베딩 처리

### 2. ImageManager

자동 정리 기능이 있는 임시 이미지 파일 관리자

### 3. HybridRetriever

향상된 문서 검색을 위해 FAISS 벡터 검색과 Elasticsearch 결합

### 4. RAGVisualizer

전체 시스템 조율
- 문서 검색
- 질의응답
- 이미지 처리
- 응답 생성

## 오류 처리

포괄적인 오류 처리와 로깅을 포함합니다.
- 모든 주요 작업에 try-except 블록 적용
- 상세한 오류 메시지 로깅
- 임시 파일 자동 정리