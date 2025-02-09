from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json, asyncio

app = FastAPI()

@app.get("/run_graph")
async def run_graph_endpoint():
    initial_state = {
        "company_name": "LG화학",
        "user_assets": 10000000.0,
        "financial_query": "2025년 3월 기준, 해당 기업의 재무 리포트 및 투자 전망 분석",
        "investment_persona": "중고위험(적극적)"
    }
    # run_graph_stream은 동기 함수이므로 asyncio.to_thread로 호출
    stream_results = await asyncio.to_thread(run_graph_stream, initial_state)
    
    async def event_generator():
        for node_name, state in stream_results:
            yield f"data: {json.dumps({'node': node_name, 'state': state}, default=str)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
