import os
from config import FAISS_INDEX_PATH

def delete_faiss_index():
    """기존 FAISS 인덱스 삭제"""
    if os.path.exists(FAISS_INDEX_PATH):
        os.remove(FAISS_INDEX_PATH)
        print(f"FAISS 인덱스 '{FAISS_INDEX_PATH}' 삭제됨.")
    else:
        print("인덱스 파일이 존재하지 않습니다.")
