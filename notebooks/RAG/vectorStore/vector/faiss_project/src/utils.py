import os
from config import settings


def delete_faiss_index(index_name: str):
    """기존 FAISS 인덱스 삭제"""
    index_path = os.path.join(
        settings.FAISS_INDEX_FOLDER_PATH, f"{index_name}.index")
    if os.path.exists(index_path):
        os.remove(index_path)
        print(f"FAISS 인덱스 '{index_path}' 삭제됨.")
    else:
        print("인덱스 파일이 존재하지 않습니다.")
