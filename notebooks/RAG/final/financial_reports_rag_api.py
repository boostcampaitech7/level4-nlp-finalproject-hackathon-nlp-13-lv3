import os
import json
import requests
import logging
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.embeddings.base import Embeddings
from langchain_core.messages import SystemMessage, HumanMessage
from elasticsearch import Elasticsearch
from pydantic import BaseModel, Field, PrivateAttr
from openai import OpenAI

# 1. 환경 변수 로드 및 OpenAI API 키 설정
load_dotenv()

# 2. 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 3. 입력/출력 모델 정의 (Pydantic)
class QueryInput(BaseModel):
    query: str

class QueryOutput(BaseModel):
    context: List[str]
    answer: str

# 4. SentenceTransformer를 이용한 임베딩 처리 클래스
class CustomSentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()

# 5. FAISS와 Elasticsearch를 결합한 하이브리드 검색기 구현
class HybridRetriever(BaseRetriever, BaseModel):
    faiss_api_key: str
    faiss_url: str = Field(default="http://3.34.62.202:8060")
    es_host: str = Field(default="http://3.34.62.202:9200")
    
    _session: Optional[requests.Session] = PrivateAttr(default=None)
    _es: Optional[Elasticsearch] = PrivateAttr(default=None)
    _model: Optional[SentenceTransformer] = PrivateAttr(default=None)
    
    def __init__(
        self, 
        api_key: str,
        faiss_url: str = "http://3.34.62.202:8060",
        es_host: str = "http://3.34.62.202:9200"
    ):
        super().__init__(
            faiss_api_key=api_key,
            faiss_url=faiss_url,
            es_host=es_host
        )
        self._session = requests.Session()
        self._es = Elasticsearch(self.es_host)
        self._model = SentenceTransformer('dragonkue/BGE-m3-ko')

    def _get_relevant_documents(self, query: str) -> List[Document]:
        try:
            # 1. FAISS 벡터 검색: 쿼리를 벡터화하여 FAISS 서버에 요청
            query_vector = self._model.encode(query).tolist()
            faiss_response = self._session.post(
                f"{self.faiss_url}/api/context/search-by-vector",
                headers={"x-api-key": self.faiss_api_key},
                json={
                    "index": "prod-labq-documents-dragonkue-doc-ver2--only-summary-faiss-hantaek",
                    "query_vector": query_vector,
                    "size": 100
                },
                timeout=15
            )
            faiss_results = faiss_response.json()['results']
            
            # 2. Elasticsearch 텍스트 검색: FAISS 결과의 문서 ID를 기반으로 검색
            nid_values = [item['document_id'] + 1 for item in faiss_results]
            es_query = {
                "query": {
                    "bool": {
                        "filter": {
                            "terms": {
                                "nid": nid_values
                            }
                        },
                        "should": {
                            "match": {
                                "text": query
                            }
                        }
                    }
                },
                "size": 15,
                "sort": [{"_score": {"order": "desc"}}]
            }
            
            es_response = self._es.search(
                index="prod-labq-documents-dragonkue-doc-ver2--only-summary-elastic-hantaek", 
                body=es_query
            )
            
            # 3. Elasticsearch 결과를 Document 객체로 변환
            documents = []
            for hit in es_response["hits"]["hits"]:
                source = hit["_source"]
                doc = Document(
                    page_content=source["text"],
                    metadata={
                        "score": hit["_score"],
                        "company_name": source["metadata"]["company_name"],
                        "category": source["metadata"].get("category", "text"),
                        "id": source["uid"],
                    }
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            return []

# 6. RAG 시스템 클래스 (QA 체인 구성 및 Groundedness Check / Query Rewrite 포함)
class RAGSystem:
    def __init__(self):
        self.embedding_model = CustomSentenceTransformerEmbeddings(
            'dragonkue/BGE-m3-ko'
        )
        
        self.hybrid_retriever = HybridRetriever(
            api_key=os.getenv("FAISS_API_KEY"),
            faiss_url="http://3.34.62.202:8060",
            es_host="http://3.34.62.202:9200"
        )
        
        self.setup_qa_chain()
        logger.info("RAG system initialization completed")

    def _get_prompt_template(self) -> PromptTemplate:
        template = """
        주어진 문서의 내용을 기반으로 아래의 규칙을 참고한 후, 핵심만 요약해서 답변해주세요.

        중요: 수치 데이터 처리 규칙
        1. 단위 보존 원칙:
        - 문서에 나온 모든 수치는 반드시 원본 단위 그대로 사용할 것
        - 예시: 
            * 2,373십억원 → 2,373십억원 (O)
            * 2,373십억원 → 23,730억원 (X)
            * 7,060십억원 → 7,060십억원 (O)
            * 7,060십억원 → 70,600억원 (X)
        
        2. 단위 표기:
        - 모든 수치는 반드시 단위를 포함하여 표기
        - 단위 변환 절대 금지
        - 십억원, 억원 등의 단위는 반드시 원문 그대로 사용

        분석 가이드라인:
        1. 출처 정보
        - 참고한 문서의 날짜
        - 증권사 및 애널리스트 정보
        - 주어진 문서에 참고한 리스트, 표 형식이 있는 경우 리스트 및 표로 출력에 포함시키세요.

        2. 시각자료 참조시
        - 차트/표의 주요 내용 
        - 데이터의 한계점
        
        3. 날짜 관계 및 정보 분석
        - 날짜의 관계 및 정보들을 분석해서 의미있는 정보로 해석해주세요. 

        질문: {question}

        문맥: {context}

        Let's solve this step by step:
        """
        return PromptTemplate(
            template=template, 
            input_variables=["context", "question"]
        )

    def setup_qa_chain(self):
        try:
            # 리랭커 모델과 압축기를 사용하여 문맥 압축
            reranker_model = HuggingFaceCrossEncoder(
                model_name="BAAI/bge-reranker-v2-m3"
            )
            compressor = CrossEncoderReranker(
                model=reranker_model,
                top_n=4
            )
            
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.hybrid_retriever
            )
            
            # ChatOpenAI 모델을 사용하여 답변 생성
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.compression_retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": self._get_prompt_template()
                }
            )         
            
        except Exception as e:
            logger.error(f"QA chain setup error: {str(e)}")
            raise

    def check_groundedness(self, answer: str, query: str) -> Tuple[bool, int, str]:
        """
        Modified to return explanation along with the score
        Returns: (평가 합격 여부, 평가 점수, 평가 설명)
        """
        try:
            prompt = f"""
                질문에 대한 답변을 1부터 10까지 점수로 평가해 주세요.
                
                (1: 전혀 근거 없음, 10: 매우 완벽하게 근거함)
                
                **평가 기준**: (1) 질문과의 관련성, (2) 핵심 내용 포함, (3) 출처 제공 여부, (4) 정확한 수치 단위 기재
                
                **질문**:
                ------------------
                {query}
                ------------------
                
                **답변**:
                ------------------
                {answer}
                ------------------
                
                반드시 아래와 같이 JSON 형식으로만 응답해 주세요 (추가 텍스트 없이):
                단, 중요사항: 평가 explanation에 부족한 정보(정보 누락)이 발생한 경우 3-5점을 차감합니다.  
                {{
                    "score": <정수, 1~10 사이>,
                    "explanation": "<각 항목별 평가 결과 요약, 부족한 점 상세 설명>"
                }}
                """
            client = OpenAI()
                
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 평가 기준에 따라 매우 엄격하게 Groundedness Check을 하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "groundedness_evaluation",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "explanation": {"type": "string"}
                            },
                            "required": ["score", "explanation"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            evaluation_text = response.choices[0].message.content.strip()
            logger.info(f"Structured Groundedness evaluation response: {evaluation_text}")
            evaluation_json = json.loads(evaluation_text)
            score = int(evaluation_json.get("score", 0))
            explanation = evaluation_json.get("explanation", "")
            return (score >= 8, score, explanation)
        except Exception as e:
            logger.error(f"Groundedness check error (JSON parsing): {str(e)}")
            return (False, 0, "Error during evaluation")

    def rewrite_query(self, original_query: str, previous_answer: str, groundedness_explanation: str) -> str:
        """
        이전 답변에서 누락된 정보만 찾도록 질문 재작성
        """
        try:
            template = """
                    원래 질문:
                    ------------------
                    {original_query}
                    ------------------

                    현재까지의 답변:
                    ------------------
                    {previous_answer}
                    ------------------

                    부족한 정보 (평가 결과):
                    ------------------
                    {groundedness_explanation}
                    ------------------

                    
                    질문 재작성 지침:
                    1. 핵심 키워드 유지:
                    - 회사명, 증권사명 등 정확한 매칭이 필요한 정보는 그대로 유지
                    - 숫자와 단위는 원본 형식 그대로 사용
                    - 분기/연도는 금융 용어 형식 사용 (1Q23, FY23 등)

                    2. 검색 효율성 고려:
                    - Faiss와 ElasticSearch 검색을 위한 정확한 키워드 사용
                    - 불필요한 조사나 문장 종결어미 제거

                    3. 누락 정보 초점:
                    - 이미 얻은 정보는 반드시 제외
                    - 평가 결과에서 지적된 부족한 정보에 집중

                    4. 간결성:
                    - 3-6개의 핵심 키워드로 구성
                    - 키워드는 공백으로 구분

                    - 예시 1)
                    원래 질문: 삼성전자의 2024년 1분기 실적 전망은 어떤가요?
                    현재 답변: 메모리 수요 회복으로 매출액은 상승이 예상됩니다.
                    부족한 점: 구체적인 수치와 증권사 리포트 출처가 없음
                    재작성 쿼리: 삼성전자 1Q24E 실적전망 매출액 증권사

                    - 예시 2)
                    원래 질문: LG화학 분기별 영업이익 추이가 궁금해요.
                    현재 답변: 3Q23 영업이익만 알려드렸습니다.
                    부족한 점: 다른 분기 정보 누락
                    재작성 쿼리: LG화학 1Q23 2Q23 4Q23E QoQ
                    
                    - 금융 용어 참고:
                        - 1Q23, 2Q23 → 23년 1분기, 2분기
                        - FY23 → 23 회계연도
                        - E → 추정/예상 (1Q24E, FY24E)
                        - YoY → 전년비, QoQ → 전분기비
                        - TTM → 최근 12개월
                        - YTD → 연초부터 현재까지

                    예시와 금융 용어를 참고해서 위 지침을 단계적으로 수행하고 새로운 검색 쿼리를 작성해주세요.
                    결과는 핵심 키워드들을 공백으로 구분하여 제시하세요. 
                    """
            
            # PromptTemplate 사용하여 프롬프트 생성
            prompt = PromptTemplate(
                template=template,
                input_variables=["original_query", "previous_answer", "groundedness_explanation"]
            )
            
            # ChatOpenAI 모델 인스턴스 생성 (낮은 temperature 사용)
            llm = ChatOpenAI(
                temperature=0.1,
                model="gpt-4o-mini"
            )
            
            # 프롬프트 포맷팅
            formatted_prompt = prompt.format(
                original_query=original_query,
                previous_answer=previous_answer,
                groundedness_explanation=groundedness_explanation
            )
            
            # 시스템 프롬프트
            system_template = """
                            당신은 하이브리드 검색 시스템을 위한 질문 재작성 전문가입니다.
                            아래의 검색 시스템을 위한 질문 재작성 지침에 따라 역할을 수행하세요.
                            
                            검색 시스템은 다음 3단계로 작동합니다:
                            1. Faiss: 의미적 유사성 기반 검색 (100개 문서 검색)
                            2. ElasticSearch: 키워드 기반 정확도 검색 (15개 문서 선별)
                            3. Reranker: 최종 관련성 기반 재정렬
                            """
            # LangChain 메시지 객체 사용
            messages = [
                SystemMessage(content=system_template),
                HumanMessage(content=formatted_prompt)
            ]
            
            # LLM 실행 및 응답 반환
            response = llm.predict_messages(messages)
            new_query = response.content.strip()
            
            logger.info(f"Rewritten query with previous answer context: {new_query}")
            return new_query
            
        except Exception as e:
            logger.error(f"Query rewriting error: {str(e)}")
            return original_query

    def combine_answers(self, previous_answer: str, new_answer: str, original_query: str) -> str:
        """
        이전 답변과 새로운 답변을 결합하여 더 완성도 높은 답변을 생성
        """
        try:
            template = f"""
                당신은 금융 분석 보고서 작성 전문가입니다. 다음 두 답변을 통합하여 하나의 완성된 답변을 만들어주세요.

                원래 질문:
                ------------------
                {original_query} 
                ------------------

                분석 단계:
                1. 질문 의도 파악:
                - 질문의 핵심 요구사항 이해
                - 사용자가 알고 싶어하는 핵심 정보 식별
                
                2. 각 답변의 정보를 분석하세요:
                - 이전 답변의 핵심 정보 파악
                - 새로운 답변에서 추가된 정보 파악
                - 질문 의도에 맞는 정보 우선순위화
                
                3. 정보 보완 관계를 파악하세요:
                - 새로운 답변이 이전 답변의 어떤 부분을 보완하는지
                - 각 답변이 질문의 어떤 측면을 다루는지
                - 질문 의도에 부합하는 정도 평가
                
                4. 수치 데이터를 검증하세요:
                - 모든 수치는 원본 단위 그대로 유지 (예: 2,373십억원 → 2,373십억원)
                - 단위 변환 금지
                - 숫자와 단위가 정확히 일치하는지 확인
                
                5. 다음 구조로 통합된 답변을 작성하세요:
                - 질문에 대한 직접적인 답변 먼저 제시
                - 핵심 정보를 우선적으로 배치
                - 부가 정보는 논리적 순서로 뒤에 배치
                - 출처나 시점 정보 포함
                
                이전 답변:
                ------------------
                {previous_answer}
                ------------------

                새로운 답변:
                ------------------
                {new_answer}
                ------------------

                최종 답변 작성시 유의사항:
                1. 원래 질문의 의도를 최우선으로 고려하세요.
                2. 두 답변의 정보를 단순히 나열하지 말고, 질문 의도에 맞게 의미있게 통합하세요.
                3. 이전 답변의 맥락을 유지하면서 새로운 정보를 자연스럽게 추가하세요.
                4. 모든 수치 데이터의 정확성을 재검증하세요.
                5. 문장 간의 자연스러운 흐름을 만드세요.

                위의 단계를 따라 통합된 답변을 작성해주세요.
            """
            
            # PromptTemplate 사용하여 프롬프트 생성
            prompt = PromptTemplate(
                template=template,
                input_variables=["previous_answer", "new_answer"]
            )
            
            # ChatOpenAI 모델 인스턴스 생성
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            
            # 프롬프트 포맷팅
            formatted_prompt = prompt.format(
                previous_answer=previous_answer,
                new_answer=new_answer
            )
            
            # LangChain 메시지 객체 사용
            messages = [
                SystemMessage(content="당신은 금융 분석 보고서 작성 전문가입니다. 당신의 역할을 여러 답변을 통합하여 질문에 대해 정확한 답변하는 것입니다."),
                HumanMessage(content=formatted_prompt)
            ]
            
            # LLM 실행 및 응답 반환
            response = llm.predict_messages(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Answer combination error: {str(e)}")
            return new_answer

    def process_query(self, query: str) -> Dict[str, any]:
        """
        Accumulated answers and Contexts를 반영
        """
        max_iterations = 3 # 최대 3번까지 시도
        iteration = 0
        current_query = query
        accumulated_answer = None
        accumulated_contexts = []  # 모든 context를 저장할 리스트
        previous_explanation = None
        
        while iteration < max_iterations:
            try:
                result = self.qa_chain(current_query)
                current_answer = result["result"]
                current_contexts = [doc.page_content for doc in result["source_documents"]]
                
                # context 누적 (중복 제거)
                accumulated_contexts.extend(ctx for ctx in current_contexts 
                                        if ctx not in accumulated_contexts)

                # 답변 누적
                if accumulated_answer:
                    accumulated_answer = self.combine_answers(accumulated_answer, current_answer, query)
                else:
                    accumulated_answer = current_answer

                # Groundedness Check - 원래 질문과 누적된 답변을 비교
                passed, score, explanation = self.check_groundedness(accumulated_answer, query)
                logger.info(f"Iteration {iteration + 1}: Groundedness score = {score}")
                
                if passed:
                    return {
                        "context": accumulated_contexts,  # 누적된 모든 context 반환
                        "answer": accumulated_answer
                    }
                else:
                    iteration += 1
                    logger.info(f"Iteration {iteration}: {score}점으로 답변의 근거성이 부족하여 질문 재작성 시도.")
                    previous_explanation = explanation
                    current_query = self.rewrite_query(query, accumulated_answer, previous_explanation)
            
            except Exception as e:
                error_msg = f"Query processing error: {str(e)}"
                logger.error(error_msg)
                return {
                    "context": accumulated_contexts,
                    "answer": f"오류가 발생하여 질문을 완전히 처리할 수 없습니다. 현재까지의 답변: {accumulated_answer or '없음'}"
                }
        
        # 최대 반복 후에도 충분한 근거성을 확보하지 못한 경우
        return {
            "context": accumulated_contexts,  # 누적된 모든 context 반환
            "answer": f"주어진 문서에서 질문에 대한 적절한 답변을 찾지 못했습니다. 다음은 현재까지 검색을 통해 누적된 답변입니다. {accumulated_answer}"
        }

# 7. FastAPI 애플리케이션 구성
app = FastAPI(title="Financial Report Analysis API with Groundedness Check")

# RAG 시스템 초기화
rag_system = RAGSystem()

@app.post("/api/query", response_model=QueryOutput)
async def process_query(query_input: QueryInput):
    try:
        result = rag_system.process_query(query_input.query)
        return QueryOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 8. 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
