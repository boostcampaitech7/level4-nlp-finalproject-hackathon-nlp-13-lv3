import pickle
from config import PICKLE_FILE_PATH


def load_documents():
    """Pickle 파일에서 문서 로드 및 검증"""
    with open(PICKLE_FILE_PATH, 'rb') as f:
        documents = pickle.load(f)

    print(f"총 {len(documents)}개의 문서가 로드되었습니다.")

    # 샘플 데이터 출력
    for i, doc in enumerate(documents[:100]):
        print(f"\n문서 {i + 1} 내용:\n{doc.page_content}")

    return documents
