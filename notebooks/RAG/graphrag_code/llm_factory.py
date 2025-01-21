# llm_factory.py
import tiktoken
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType

from config import API_KEY, LLM_MODEL, EMBEDDING_MODEL

def create_llm(api_key: str = API_KEY,
               model_name: str = LLM_MODEL,
               max_retries: int = 20) -> ChatOpenAI:
    """
    OpenAI ChatGPT(또는 유사) ChatOpenAI 인스턴스를 생성
    """
    return ChatOpenAI(
        api_key=api_key,
        model=model_name,
        api_type=OpenaiApiType.OpenAI,
        max_retries=max_retries,
    )


def create_text_embedder(api_key: str = API_KEY,
                         model_name: str = EMBEDDING_MODEL,
                         max_retries: int = 20) -> OpenAIEmbedding:
    """
    OpenAI Embedding 인스턴스를 생성
    """
    return OpenAIEmbedding(
        api_key=api_key,
        api_base=None,
        api_type=OpenaiApiType.OpenAI,
        model=model_name,
        deployment_name=model_name,
        max_retries=max_retries,
    )


def create_token_encoder(encoding_name: str = "cl100k_base"):
    """
    tiktoken 인코더를 생성
    """
    return tiktoken.get_encoding(encoding_name)
