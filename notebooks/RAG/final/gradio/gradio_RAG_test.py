import os
import base64
import gradio as gr
import atexit
import uuid
import shutil
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
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
from PIL import Image
import io

# 환경변수 설정
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class CustomSentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()

class ImageManager:
    def __init__(self, base_dir: str = "temp_images"):
        self.base_dir = base_dir
        self.temp_files: Set[str] = set()
        self.cleanup_threshold = 100
        
        os.makedirs(self.base_dir, exist_ok=True)
        atexit.register(self.cleanup_all)
    
    def save_image(self, image: Image.Image) -> Optional[str]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp_image_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.base_dir, filename)
            
            image.save(filepath)
            self.temp_files.add(filepath)
            
            if len(self.temp_files) > self.cleanup_threshold:
                self._cleanup_old_files()
            
            return filepath
        except Exception as e:
            logger.error(f"이미지 저장 오류: {str(e)}")
            return None

    def _cleanup_old_files(self, keep_recent: int = 20):
        try:
            files = sorted(self.temp_files, key=os.path.getctime)
            files_to_remove = files[:-keep_recent]
            
            for filepath in files_to_remove:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.temp_files.remove(filepath)
        except Exception as e:
            logger.error(f"파일 정리 중 오류 발생: {str(e)}")
    
    def cleanup_all(self):
        try:
            for filepath in self.temp_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
            self.temp_files.clear()
            
            if os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir)
        except Exception as e:
            logger.error(f"전체 정리 중 오류 발생: {str(e)}")

class HybridRetriever(BaseRetriever, BaseModel):
    faiss_api_key: str
    faiss_url: str = Field(default="http://3.34.62.202:8060")
    es_host: str = Field(default="http://3.34.62.202:9200")
    
    # private 속성 선언
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
            # 1. FAISS 벡터 검색
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
            
            # 2. Elasticsearch 검색
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
                "sort": [
                    {
                        "_score": {
                            "order": "desc"
                        }
                    }
                ]
            }
            
            es_response = self._es.search(
                index="prod-labq-documents-dragonkue-bge-m3-ko-elastic-hantaek", 
                body=es_query
            )
            
            # 3. 결과를 Document 객체로 변환
            documents = []
            for hit in es_response["hits"]["hits"]:
                source = hit["_source"]
                doc = Document(
                    page_content=source["text"],
                    metadata={
                        "score": hit["_score"],
                        "company_name": source["metadata"]["company_name"],
                        "category": source["metadata"].get("category", "text"),
                        "base64_encoding": source["metadata"].get("base64_encoding"),
                        "id": source["uid"],
                        "source": "hybrid_search"
                    }
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"하이브리드 검색 중 오류 발생: {str(e)}")
            return []

class RAGVisualizer:
    def __init__(self):
        self.embedding_model = CustomSentenceTransformerEmbeddings(
            'dragonkue/BGE-m3-ko'
        )
        
        # 하이브리드 리트리버 초기화
        self.hybrid_retriever = HybridRetriever(
            api_key=os.getenv("FAISS_API_KEY"),
            faiss_url="http://3.34.62.202:8060",
            es_host="http://3.34.62.202:9200"
        )
        
        self.image_manager = ImageManager()
        self.setup_qa_chain()
        logger.info("RAG system initialization completed")

    def _get_prompt_template(self) -> PromptTemplate:
        template = """
        주어진 문서의 내용을 기반으로 답변해주세요.

        중요: 수치 데이터 처리 규칙
        - 모든 수치는 반드시 문서에 있는 그대로의 단위를 사용할 것 (예: 십억원은 십억원 그대로, 억원으로 변환하지 말 것)
        - 수치 언급시 항상 단위를 함께 표기
        - 단위 임의 변환 절대 금지

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
        1) First, carefully identify all numbers and their exact units from the context
        2) Double-check that we maintain the original units without any conversion
        3) Then, analyze other aspects of the information
        4) Finally, formulate the answer while ensuring unit accuracy
        """
        return PromptTemplate(
            template=template, 
            input_variables=["context", "question"]
            )

    def setup_qa_chain(self):
        try:
            # 리랭커 설정
            reranker_model = HuggingFaceCrossEncoder(
                model_name="BAAI/bge-reranker-v2-m3"
            )
            compressor = CrossEncoderReranker(
                model=reranker_model,
                top_n=5
            )
            
            # 하이브리드 리트리버를 압축 리트리버와 결합
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.hybrid_retriever
            )
            
            # QA 체인 설정
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
            logger.error(f"QA 체인 설정 중 오류 발생: {str(e)}")
            raise

    def decode_base64_to_image(self, base64_string: str) -> Optional[Image.Image]:
        try:
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            logger.error(f"이미지 디코딩 오류: {str(e)}")
            return None

    def process_query(self, query: str) -> Tuple[str, List[str]]:
        try:
            result = self.qa_chain(query)
            answer = result["result"]
            source_docs = result["source_documents"]
            
            image_paths = []
            visual_elements_processed = set()
            
            for doc in source_docs:
                metadata = doc.metadata
                if metadata["category"] in ["table", "chart", "figure"]:
                    if metadata["id"] not in visual_elements_processed:
                        base64_str = metadata.get("base64_encoding")
                        if base64_str:
                            image = self.decode_base64_to_image(base64_str)
                            if image:
                                image_path = self.image_manager.save_image(image)
                                if image_path:
                                    image_paths.append(image_path)
                                    visual_elements_processed.add(metadata["id"])
            
            return answer, image_paths
        except Exception as e:
            error_msg = f"질문 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return error_msg, []

def create_gradio_interface():
    rag_visualizer = RAGVisualizer()
    
    with gr.Blocks() as demo:
        gr.Markdown("# Financial Report Analysis System")
        
        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="질문을 입력하세요",
                    placeholder="예: 24년도 크래프톤의 재무제표를 분석하고 25년도의 투자전략을 제안해주세요."
                )
                answer_output = gr.Textbox(
                    label="답변",
                    lines=10
                )
            
            with gr.Column(scale=1):
                gallery = gr.Gallery(
                    label="관련 시각자료",
                    show_label=True,
                    columns=[1],
                    rows=[1],
                    height="auto"
                )
        
        query_input.submit(
            fn=rag_visualizer.process_query,
            inputs=[query_input],
            outputs=[answer_output, gallery]
        )
    
    return demo

if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(show_api=False)