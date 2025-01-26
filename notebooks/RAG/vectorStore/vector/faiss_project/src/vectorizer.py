import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from src.data_loader import load_documents
import pickle
from config import FAISS_INDEX_PATH, FAISS_DIMENSION, PICKLE_FILE_PATH

# 절대 경로 변환 (보완)
FAISS_INDEX_FOLDER_PATH = os.path.abspath(settings.FAISS_INDEX_FOLDER_PATH)

# 모델 로딩 (384차원 모델)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def create_faiss_index(index_name: str, algorithm: int, dimension: int):
    """
    FAISS 인덱스를 생성하고, 주어진 텍스트에 대한 벡터를 인덱스에 추가하는 함수.
    """

    # 문서 로드
    documents = load_documents()

    # 텍스트 추출 (page_content만 사용)
    texts = [doc.page_content for doc in documents]  # 데이터 클래스 형태로 접근

    # 텍스트를 한 번에 임베딩
    embeddings = model.encode(texts, convert_to_numpy=True)

    # 처음 10개의 문서 출력 (처음 100자만 표시)
    for i, text in enumerate(texts[:10]):
        print(f"문서 {i+1}: {text[:100]}...")  # 문서의 처음 100자만 출력

    # 기존 경로가 파일이면 삭제
    if os.path.isfile(FAISS_INDEX_PATH):
        os.remove(FAISS_INDEX_PATH)

    # 디렉토리 존재 여부 확인 후 생성
    if not os.path.exists(FAISS_INDEX_FOLDER_PATH):
        try:
            os.makedirs(FAISS_INDEX_FOLDER_PATH)
        except Exception as e:
            return False, f"디렉토리 생성 실패: {str(e)}"

    index_file = os.path.join(FAISS_INDEX_FOLDER_PATH, f"{index_name}.index")

    dimension = dimension if dimension else settings.FAISS_DIMENSION
    try:
        # 알고리즘 선택에 따른 인덱스 생성
        if algorithm == 1:
            index = faiss.IndexFlatL2(dimension)  # 384 차원
        elif algorithm == 2:
            nlist = 100
            quantizer = faiss.IndexFlatL2(dimension)  # 384 차원
            index = faiss.IndexIVFFlat(
                quantizer, dimension, nlist, faiss.METRIC_L2)
            index.train(np.random.random(
                (1000, dimension)).astype('float32'))
        elif algorithm == 3:
            index = faiss.IndexHNSWFlat(dimension, 32)  # 384 차원
        else:
            return False, "잘못된 알고리즘 번호입니다."  # 잘못된 알고리즘 번호 처리

        # 벡터를 인덱스에 추가
        index.add(embeddings)
        print(f"{len(embeddings)}개의 벡터가 인덱스에 추가되었습니다.")

        # 인덱스에 추가된 벡터 수 출력
        print(f"현재 인덱스에 저장된 총 벡터 수: {index.ntotal}")

        # 인덱스를 파일로 저장
        faiss.write_index(index, index_file)
        print(f"FAISS 인덱스 생성 완료: {index_file}")
        return True, f"인덱스를 성공적으로 생성하였습니다: {index_name}"

    except Exception as e:
        return False, f"인덱스 생성 중 오류 발생: {str(e)}"
