# PDF Parsing Process

증권사 리포트 PDF 파일들을 처리하여 pickle( Langchain에서 지원하는 형식: Document )로 변환하는 코드입니다.

## 주요 기능
- PDF 파일을 JSON으로 변환 (Upstage Document Parse API 사용)
- 문서 내 표, 차트, 이미지 추출 및 base64 인코딩 저장
- 메타데이터(회사명, 날짜, 증권사 등) 자동 추출
- 검색 가능한 Document 객체로 변환
- pickle 형태로 저장하여 재사용 가능

## 설치 방법
0. `Poetry version 2.0.1`를 사용해주세요.

1. 필요한 패키지 설치
```bash
poetry install
```

2. shell 플러그인 설치
```bash
poetry self add poetry-plugin-shell
```

3. 가상환경 실행
```bash
poetry shell
``` 

4. `.env` 파일 생성 및 API 키 설정
```
UPSTAGE_API_KEY="your-api-key-here"
```

## 디렉토리 구조
```
project_root/
├── .env                 # API 키 설정 파일
├── process_pdf.py      # 메인 스크립트
├── pyproject.toml       # 의존성 패키지 목록
├── poetry.lock
├── pdf_files/           # PDF 파일 디렉토리
│   ├── CJ제일제당_20241120_신한증권.pdf
│   └── ...
├── pdf_files/processed/ # JSON 파일 저장 디렉토리 (자동 생성)
│   ├── CJ제일제당_20241120_신한증권.json
│   └── ...
└── documents.pkl        # 최종 생성되는 pickle 파일
```

## PDF 파일명 규칙
PDF 파일명은 다음 형식을 따라야 합니다:
```
{회사명}_{날짜(YYYYMMDD)}_{증권사}.pdf
예: CJ제일제당_20241120_신한증권.pdf
```

## 사용 방법
1. PDF 파일들을 `pdf_files` 디렉토리에 위치시킵니다.
2. 스크립트 실행
```bash
python process_pdf.py
```

## 생성되는 Documents 객체 구조

pickle로 저장되는 `documents.pkl` 파일에는 Document 객체들의 리스트가 포함됩니다.

### Document 객체 구조
```python
Document(
    # 페이지 내용 (마크다운 형식) ---------------- 임베딩 될 부분
    page_content: str,
    
    # 메타데이터
    metadata: {
        # 기본 메타데이터
        "category": str,          # "text", "table", "chart", "figure" 중 하나
        "coordinates": list,      # 페이지 내 위치 좌표
        "page": int,             # 페이지 번호
        "id": str,               # 요소 고유 ID
        
        # 파일 관련 메타데이터
        "company_name": str,      # 회사명
        "report_date": str,       # 리포트 날짜 (YYYYMMDD)
        "securities_firm": str,   # 증권사명
        "source_file": str,       # 원본 PDF 파일명
        
        # 시각 요소의 경우 (표, 차트, 이미지)
        "base64_encoding": str,   # base64 인코딩된 이미지 데이터
        
        # 컨텐츠 타입
        "content_types": {
            "markdown": str,      # 마크다운 형식
            "text": str,          # 일반 텍스트
            "html": str           # HTML 형식
        }
    }
)
```

### Pickle 파일 사용 예시
```python
import pickle
from typing import List
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Pickle 파일 로드
with open('documents.pkl', 'rb') as f:
    documents: List[Document] = pickle.load(f)

# 예시 : 전체 문서로 Chroma DB 생성
embeddings = OpenAIEmbeddings()
vector_db = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="all_reports"
)
```

## 주의사항
1. PDF 파일명은 지정된 형식을 정확히 따라야 합니다.
2. API 키는 반드시 `.env` 파일에 설정되어 있어야 합니다.
3. 생성된 JSON 파일은 `pdf_files/processed/` 디렉토리에 보관됩니다.
4. 처리 중 발생하는 모든 오류는 로그에 기록됩니다.

## 로깅 처리
처리 과정 중의 모든 로그는 다음과 같은 형식으로 출력됩니다:
```
2024-01-20 10:00:00,000 - INFO - 총 5개의 PDF 파일 처리 시작
2024-01-20 10:00:01,000 - INFO - 처리 중 (1/5): CJ제일제당_20241120_신한증권.pdf
...
```
