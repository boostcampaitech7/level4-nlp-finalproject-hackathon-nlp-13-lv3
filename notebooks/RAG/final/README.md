## 1. 개요 

1. **FAISS와 Elasticsearch**를 결합한 하이브리드 검색 (**Hybrid Retriever**)을 통해 우선적으로 후보 문서를 찾습니다.  
2. **Cross Encoder 기반 리랭킹** (**ContextualCompressionRetriever**)으로 문서 목록을 압축합니다. 
3. **gpt-4o-mini**를 통해 최종 답변을 생성합니다.
4. 추가적으로 답변의 신뢰도(근거성, **Groundedness**)를 점수화하여 부족하면 자동으로 질문 재작성을 시도하고, 답변을 결합(**combine**)해가며 더욱 완성도 높은 답변을 만들어냅니다.

---

## 2. 주요 함수별 설명

- **`process_query`**  
  : 사용자가 입력한 query를 받아서 **qa_chain (RetrievalQA)**으로 문서 검색 및 답변을 생성합니다.  
    - 이때, **Groundedness (근거성)** 점수가 충분치 않으면 (score < 8), **`rewrite_query`**를 통해 질문을 재작성합니다.  
    - 최대 3번 반복 후에도 점수가 낮으면 “답변 불가” 메시지와 함께 누적된 답변을 반환합니다.

- **`check_groundedness`**  
  : 질문과 답변을 대조하여 1~10 사이의 점수를 매깁니다.  
    - 평가 항목: 질문 관련성, 핵심 내용 포함, 출처 포함, 수치 단위 정확성 등.

- **`rewrite_query`**  
  : 이전 답변에서 누락된 정보를 바탕으로 검색 키워드를 재조합합니다.  
    - “이미 얻은 정보”는 제외하고, “부족한 정보”를 중심으로 검색 효율에 맞게 쿼리를 짧고 핵심 키워드 형태로 변경합니다.

- **`combine_answers`**  
  : 이전 답변과 새 답변을 합쳐서 좀 더 완성도 높은 하나의 답변을 만들어 냅니다.  
    - 금융 보고서 작성 문체(단계적 분석 + 최종 통합)로 자연스럽게 서술하며, 수치 단위 변환을 엄격히 제한합니다.

- **`HybridRetriever`**  
  1) **FAISS**: 쿼리 임베딩 벡터화 → 서버 요청 → 100개 문서 ID 후보 
  2) **Elasticsearch**: 해당 문서 ID를 토대로 15개를 텍스트 검색 → **Document** 리스트 변환 
  3) 내부적으로 **SentenceTransformer('dragonkue/BGE-m3-ko')** 임베딩 모델을 사용합니다. 

---

## 3. 사용 예시

1. **`.env` 파일 준비**  
   - 다음과 같은 환경 변수를 `.env` 파일에 넣습니다. 
     ```bash
     FAISS_API_KEY=<your_api_key>
     OPENAI_API_KEY=<your_openai_key>
     ```  


2. **서버 실행**  
   ```bash
   uvicorn financial_reports_rag_api:app --host 0.0.0.0 --port 8000
   ```  
   - 또는 `python financial_reports_rag_api.py`로 바로 실행이 가능합니다.

3. **테스트 (예시)**  
   - `POST /api/query` 엔드포인트에 JSON을 전송합니다.  
   - 예:  
     ```bash
     curl -X POST -H "Content-Type: application/json" \
       -d '{"query": "삼성전자 2024년 실적 전망 알려줘"}' \
       http://localhost:8000/api/query
     ```  
   - 결과로 `{"context": [...], "answer": "..."}` 형태의 JSON 응답을 받게 됩니다. 

---

## 4. 패키지 설정

- 필요한 패키지 설정은 `./gradio/pyproject.toml`을 참고해주세요.
