import pickle
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
from app.config import EMBEDDING_MODEL

# ✅ 모델과 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)  # 토크나이저 초기화
model = AutoModel.from_pretrained(EMBEDDING_MODEL)          # 모델 초기화

def load_pickle(file_content):
    """
    업로드된 피클 파일을 읽어 리스트로 변환.
    """
    data = pickle.loads(file_content)

    if not isinstance(data, list) or not all(hasattr(doc, "page_content") for doc in data):
        raise ValueError("피클 파일은 'page_content' 속성을 가진 객체 리스트여야 합니다.")

    return [doc.page_content for doc in data]

def get_embedding(text):
    """
    개별 문서 임베딩 수행
    """
    text = f"query: {text}"  # E5 모델 특성에 맞게 프리픽스 추가
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)  # ✅ tokenizer 정의됨

    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1)  # Mean Pooling

    return embedding.squeeze().numpy()
