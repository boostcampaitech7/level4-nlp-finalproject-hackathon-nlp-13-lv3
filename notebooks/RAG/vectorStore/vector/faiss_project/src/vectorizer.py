import faiss
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, FAISS_INDEX_PATH
from src.data_loader import load_documents


def create_faiss_index():
    """FAISS 인덱스 생성 및 저장"""
    documents = load_documents()
    model = SentenceTransformer(EMBEDDING_MODEL)

    # 문서 임베딩 생성
    embeddings = model.encode([doc.page_content for doc in documents], convert_to_numpy=True)

    # FAISS 인덱스 생성
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 인덱스 저장
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"FAISS 인덱스가 '{FAISS_INDEX_PATH}'에 저장되었습니다.")
