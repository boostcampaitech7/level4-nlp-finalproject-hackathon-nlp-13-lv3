import os
import json
import glob
import pickle
import logging
import requests
from typing import Dict, List, Tuple, Optional
from langchain.schema import Document
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        """PDF 처리기 초기화"""
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError(".env 파일에 UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
        
        # 처리된 JSON 파일 저장 디렉토리 생성
        self.processed_dir = "./pdf_files/processed"
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def process_pdf_to_json(self, pdf_path: str) -> Optional[str]:
        """Upstage API를 사용하여 PDF를 JSON으로 변환"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            with open(pdf_path, "rb") as f:
                files = {"document": f}
                config = {
                    "ocr": "auto",
                    "coordinates": True,
                    "output_formats": '["html", "text", "markdown"]',
                    "model": "document-parse-250116",
                    "base64_encoding": '["figure", "chart", "table"]'
                }
                
                response = requests.post(
                    "https://api.upstage.ai/v1/document-ai/document-parse",
                    headers=headers,
                    data=config,
                    files=files,
                )
                response.raise_for_status()
                
                # JSON 파일 저장
                filename = os.path.basename(pdf_path)
                json_path = os.path.join(
                    self.processed_dir, 
                    f"{os.path.splitext(filename)[0]}.json"
                )
                
                with open(json_path, "w", encoding='utf-8') as f:
                    json.dump(response.json(), f, ensure_ascii=False, indent=2)
                
                return json_path
                
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생 ({pdf_path}): {str(e)}")
            return None
    
    def parse_filename(self, filename: str) -> Tuple[str, str, str]:
        """파일명에서 메타데이터 추출"""
        try:
            name_parts = os.path.splitext(filename)[0].split('_')
            company_name = name_parts[0]
            date = name_parts[1]
            securities_firm = name_parts[2]
            return company_name, date, securities_firm
        except Exception as e:
            logger.error(f"파일명 파싱 오류 ({filename}): {str(e)}")
            return ("unknown", "unknown", "unknown")
    
    def create_document_with_metadata(self, 
                                    element: Dict, 
                                    company_name: str, 
                                    date: str, 
                                    securities_firm: str,
                                    source_file: str) -> Document:
        """메타데이터를 포함한 Document 객체 생성"""
        try:
            metadata = {
                # 기본 메타데이터
                "category": element["category"],
                "coordinates": element["coordinates"],
                "page": element["page"],
                "id": element["id"],
                
                # 추가 메타데이터
                "company_name": company_name,
                "report_date": date,
                "securities_firm": securities_firm,
                "source_file": source_file
            }
            
            # 시각 요소인 경우 base64 인코딩 추가
            if element["category"] in ["table", "chart", "figure"]:
                if "base64_encoding" in element:
                    metadata["base64_encoding"] = element["base64_encoding"]
            
            # 컨텐츠 정보 추가
            metadata["content_types"] = {
                "markdown": element["content"]["markdown"],
                "text": element["content"]["text"],
                "html": element["content"].get("html", "")
            }
            
            return Document(
                page_content=element["content"]["markdown"],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Document 생성 중 오류: {str(e)}")
            return None
    
    def process_directory(self, pdf_dir: str, output_pickle: str) -> None:
        """PDF 디렉토리 처리 및 pickle 파일 생성"""
        try:
            documents = []
            pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
            total_files = len(pdf_files)
            
            logger.info(f"총 {total_files}개의 PDF 파일 처리 시작")
            
            for idx, pdf_file in enumerate(pdf_files, 1):
                filename = os.path.basename(pdf_file)
                logger.info(f"처리 중 ({idx}/{total_files}): {filename}")
                
                # PDF를 JSON으로 변환
                json_path = self.process_pdf_to_json(pdf_file)
                if not json_path:
                    continue
                
                # 파일명에서 메타데이터 추출
                company_name, date, securities_firm = self.parse_filename(filename)
                
                # JSON 파일 처리
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 각 요소에 대해 Document 생성
                for element in json_data["elements"]:
                    doc = self.create_document_with_metadata(
                        element,
                        company_name,
                        date,
                        securities_firm,
                        filename
                    )
                    if doc:
                        documents.append(doc)
            
            # Pickle 파일로 저장
            with open(output_pickle, 'wb') as f:
                pickle.dump(documents, f)
            
            logger.info(f"처리 완료: {len(documents)}개의 Document 생성됨")
            logger.info(f"Pickle 파일 저장됨: {output_pickle}")
            
        except Exception as e:
            logger.error(f"디렉토리 처리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    # 경로 설정
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PDF_DIR = os.path.join(BASE_DIR, "pdf_files")
    OUTPUT_PICKLE = os.path.join(BASE_DIR, "updated_documents.pkl")
    
    # PDF 처리기 생성 및 실행
    try:
        processor = PDFProcessor()
        processor.process_directory(PDF_DIR, OUTPUT_PICKLE)
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
