from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# Elasticsearch 클라이언트 설정
es = Elasticsearch("http://localhost:9200")

# 1. 텍스트 임베딩 모델 로드 (Hugging Face SentenceTransformer)
model = SentenceTransformer('all-MiniLM-L6-v2')  # 예제 모델

# 2. 텍스트 데이터를 벡터로 변환
text = "Elasticsearch is a distributed, RESTful search engine."
vector = model.encode(text).tolist()  # 벡터를 리스트로 변환

# 3. Elasticsearch 인덱스 생성 (dense_vector 필드 포함)
index_name = "text_vectors"
if not es.indices.exists(index=index_name):
    es.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": len(vector)  # 벡터 차원 수
                    }
                }
            }
        }
    )

# 4. Elasticsearch에 데이터 삽입
doc = {
    "text": text,
    "embedding": vector
}
response = es.index(index=index_name, body=doc)
print("Document indexed:", response)

# 5. Elasticsearch에서 벡터 검색 (예: 코사인 유사도)
query_vector = model.encode("Find documents about search engines").tolist()
search_response = es.search(
    index=index_name,
    body={
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": """
                    cosineSimilarity(params.query_vector, 'embedding') + 1.0
                    """,
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }
)
print("query vector", query_vector)

print("Search results:")
for hit in search_response['hits']['hits']:
    print(hit["_source"]["text"], "-> Score:", hit["_score"])
