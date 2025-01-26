import pickle
from config import settings


def load_documents():
    """Pickle 파일에서 문서 로드 및 검증"""
    with open(PICKLE_FILE_PATH, 'rb') as f:
        documents = pickle.load(f)

    print(f"총 {len(documents)}개의 문서가 로드되었습니다.")


    return documents
