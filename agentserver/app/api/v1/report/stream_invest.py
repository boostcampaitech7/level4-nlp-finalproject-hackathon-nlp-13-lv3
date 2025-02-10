# app/api/v1/report/stream_invest.py
import time
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.graph import run_graph

router = APIRouter()

@router.get("/")
async def stream_invest(
    target_company: str = Query(...),
    persona: str = Query(...)
):
    """
    Streaming API:
    GET /api/v1/report/stream-invest?target_company=xxx&persona=yyy
    SSE 형식으로 각 단계 메시지 전송
    """
    async def event_generator():
        initial_state = {
            "company_name": target_company,
            "investment_persona": persona
        }
        steps = run_graph(initial_state)
        for node_name, state in steps:
            msg = state.get(f"{node_name}_status_message", "No message")
            st = state.get(f"{node_name}_status", "inprogress")
            data = {
                "agent": node_name,
                "message": msg,
                "status": st
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            time.sleep(1)  # Optional delay

        # 최종 단계 완료 시 추가 메시지
        yield "data: {\"message\": \"All steps completed.\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")