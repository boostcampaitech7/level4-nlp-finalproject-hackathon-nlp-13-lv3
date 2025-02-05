import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging
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
from elasticsearch import Elasticsearch
from pydantic import BaseModel, Field, PrivateAttr
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Input/Output models
class QueryInput(BaseModel):
    query: str

class QueryOutput(BaseModel):
    context: List[str]
    answer: str

class CustomSentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()

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
            # 1. FAISS vector search
            query_vector = self._model.encode(query).tolist()
            faiss_response = self._session.post(
                f"{self.faiss_url}/api/context/search-by-vector",
                headers={"x-api-key": self.faiss_api_key},
                json={
                    "index": "prod-labq-documents-dragonkue-BGE-m3-ko-faiss-hantaek",
                    "query_vector": query_vector,
                    "size": 100
                },
                timeout=15
            )
            faiss_results = faiss_response.json()['results']
            
            # 2. Elasticsearch search
            nid_values = [item['document_id']+1 for item in faiss_results]
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
                index="prod-labq-documents-dragonkue-bge-m3-ko-elastic-hantaek", 
                body=es_query
            )
            
            # 3. Convert results to Document objects
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
        주어진 문서의 내용을 기반으로 답변해주세요.

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
        
        3. 데이터 검증:
        - 응답 전 모든 수치와 단위를 원본과 재확인
        - 단위 변환이 발생했다면 즉시 원본 단위로 정정

        분석 가이드라인:
        1. 출처 정보
        - 참고한 문서의 날짜
        - 증권사 및 애널리스트 정보

        2. 정성적 분석
        - 투자의견/전망의 근거
        - 시장/산업 맥락
        - 리스크 요인

        3. 시각자료 참조시
        - 차트/표의 주요 내용
        - 데이터의 한계점

        질문: {question}

        문맥: {context}

        Let's solve this step by step:
        1) First, carefully identify all numbers and their EXACT units from the context
        2) Double-check that we preserve the original units without ANY conversion
        3) Then, analyze other aspects of the information
        4) Finally, formulate the answer while ensuring unit accuracy
        5) Before sending, verify one last time that all units match the original text exactly
        """
        return PromptTemplate(
            template=template, 
            input_variables=["context", "question"]
        )

    def setup_qa_chain(self):
        try:
            reranker_model = HuggingFaceCrossEncoder(
                model_name="BAAI/bge-reranker-v2-m3"
            )
            compressor = CrossEncoderReranker(
                model=reranker_model,
                top_n=5
            )
            
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.hybrid_retriever
            )
            
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini") 
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

    def process_query(self, query: str) -> Dict[str, any]:
        try:
            result = self.qa_chain(query)
            
            # Extract answer and context
            answer = result["result"]
            context = [doc.page_content for doc in result["source_documents"]]
            
            return {
                "context": context,
                "answer": answer
            }
        except Exception as e:
            error_msg = f"Query processing error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

# FastAPI app
app = FastAPI(title="Financial Report Analysis API")

# Initialize RAG system
rag_system = RAGSystem()

@app.post("/api/query", response_model=QueryOutput)
async def process_query(query_input: QueryInput):
    try:
        result = rag_system.process_query(query_input.query)
        return QueryOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

