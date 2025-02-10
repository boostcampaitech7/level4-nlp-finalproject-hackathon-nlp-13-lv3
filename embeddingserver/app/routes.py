from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
import logging
import orjson
from app.embedding import get_embedding, load_pickle

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/app/embed-pickle", summary="Upload pickle file and get streaming embeddings")
async def embed_pickle(file: UploadFile = File(...), request: Request = None):
    """
    피클 파일을 업로드하고, 문서를 개별적으로 임베딩한 후 즉시 스트리밍 방식으로 반환합니다.
    클라이언트 연결이 끊기면 스트리밍을 중단합니다.
    """
    try:
        logger.info(f"파일 업로드됨: {file.filename}")

        # 피클 파일 읽기
        file_content = await file.read()
        texts = load_pickle(file_content)

        logger.info(f"총 {len(texts)} 개의 문서가 로드됨.")

        # ✅ 클라이언트 연결 상태 감지
        async def embedding_generator():
            for text in texts:
                # 연결이 끊겼는지 확인
                if await request.is_disconnected():
                    logger.warning("❌ 클라이언트 연결이 끊어졌습니다. 스트리밍 중단.")
                    break  # 연결이 끊기면 반복 중단

                embedding = get_embedding(text)  # 개별 문서 임베딩 수행
                yield orjson.dumps({"text": text, "embedding": embedding.tolist()}) + b"\n"

        return StreamingResponse(embedding_generator(), media_type="application/json")

    except Exception as e:
        logger.error(f"임베딩 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
