from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Field, SQLModel, Session, select
import uuid
import time
import json
import asyncio

##############################
#   MODELS & SCHEMAS
##############################

class InvestTask(SQLModel, table=True):
    """
    invest_task 테이블
    - 파라미터 4개 + task_id, status, status_message
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    invest_type: str
    company_name: str
    company_code: str
    status: str = Field(default="inprogress")         # "inprogress", "success", "failed", ...
    status_message: str = Field(default="Task created, waiting to start.")

class InvestTaskCreate(SQLModel):
    """
    요청 바디(4개 파라미터)
    """
    user_id: str
    invest_type: str
    company_name: str
    company_code: str

class InvestTaskMinimalResponse(SQLModel):
    """
    응답 바디 (user_id, task_id, status)
    """
    user_id: str
    task_id: str
    status: str

##############################
#   DB / DEPENDENCIES
##############################

from app.db.session import get_db, engine  # get_db: 세션 종속성, engine: DB 엔진

##############################
#   GRAPH / LANGRAPH 파이프라인
##############################

def run_graph(initial_state: dict):
    """
    langgraph 파이프라인 과정 중 일어나는 상황을 순차적으로 yield하는 예시 함수.
    실제로는 FinancialStatementsAnalysisAgent, NewsAnalysisAgent 등 여러 노드를 순회.
    여기서는 간단히 3단계 시뮬레이션만 예시로 작성.
    """
    # 단계 1
    initial_state["step1_status_message"] = "전문가 에이전트가 자료 수집 중..."
    initial_state["step1_status"] = "inprogress"
    yield ("Step1Agent", initial_state.copy())
    time.sleep(2)  # 시뮬레이션

    # 단계 2
    initial_state["step2_status_message"] = "분석가 리포트 생성 중..."
    initial_state["step2_status"] = "inprogress"
    yield ("Step2Agent", initial_state.copy())
    time.sleep(2)

    # 최종 단계
    initial_state["final_status_message"] = "최종 리포트 생성 완료"
    initial_state["final_status"] = "success"
    initial_state["final_report"] = "실제 최종 리포트 내용이 들어갑니다."
    yield ("FinalAnalysisAgent", initial_state.copy())

##############################
#   HELPER FUNCTIONS
##############################

def update_task_status(task_id: str, status: str, status_message: str) -> None:
    """
    주어진 task_id에 해당하는 InvestTask 레코드를 업데이트합니다.
    """
    with Session(engine) as db:
        task = db.exec(select(InvestTask).where(InvestTask.task_id == task_id)).first()
        if not task:
            print(f"[ERROR] Task {task_id} not found.")
            return
        task.status = status
        task.status_message = status_message
        db.add(task)
        db.commit()

##############################
#   ROUTER
##############################

router = APIRouter()

##############################
# 1) No-Streaming API
##############################

@router.post("/no-stream-invest", response_model=InvestTaskMinimalResponse)
def no_stream_invest_task(
    task_in: InvestTaskCreate,
    db: Session = Depends(get_db)
):
    """
    요청(4개 파라미터)을 받아 invest_task 레코드를 생성하고,
    langgraph 파이프라인(run_graph)을 동기적으로 실행합니다.
    각 단계마다 DB의 status, status_message를 업데이트하고,
    최종 상태가 success가 되면 user_id, task_id, status를 반환합니다.
    """
    # 1. invest_task 생성
    new_task = InvestTask(
        user_id=task_in.user_id,
        invest_type=task_in.invest_type,
        company_name=task_in.company_name,
        company_code=task_in.company_code,
        status="inprogress",
        status_message="Task created, waiting to start."
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 2. 초기 상태 구성
    initial_state = {
        "user_id": new_task.user_id,
        "invest_type": new_task.invest_type,
        "company_name": new_task.company_name,
        "company_code": new_task.company_code
    }

    # 3. run_graph 실행 (동기)
    intermediate_steps = []
    for node_name, state in run_graph(initial_state):
        intermediate_steps.append((node_name, state))
        # node_name과 state를 이용해 DB에 중간 상태 업데이트
        # 예: step1_status, step2_status ...
        if node_name == "Step1Agent":
            update_task_status(new_task.task_id, "inprogress", state["step1_status_message"])
        elif node_name == "Step2Agent":
            update_task_status(new_task.task_id, "inprogress", state["step2_status_message"])
        elif node_name == "FinalAnalysisAgent":
            update_task_status(new_task.task_id, "success", state["final_status_message"])

    # 4. 최종 상태를 DB에서 다시 조회
    db.refresh(new_task)
    # 응답: user_id, task_id, status
    return InvestTaskMinimalResponse(
        user_id=new_task.user_id,
        task_id=new_task.task_id,
        status=new_task.status
    )

##############################
# 2) Streaming API
##############################

@router.get("/stream-invest")
async def stream_invest_report(
    target_company: str = Query(...),
    persona: str = Query(...)
):
    """
    클라이언트로부터 회사 정보(target_company), 페르소나(persona)를 GET 쿼리로 받는다.
    langgraph 파이프라인을 비동기적으로 진행하면서 SSE 형식으로 중간 상태를 반환한다.
    """

    async def event_generator():
        # 간단히 run_graph를 호출해 에이전트 진행 상황 시뮬레이션
        initial_state = {
            "target_company": target_company,
            "persona": persona
        }
        # 노드별로 yield
        for node_name, state in run_graph(initial_state):
            # node_name, state를 SSE 형식으로 반환
            message = {
                "agent": node_name,
                "status": state.get("final_status", state.get(f"{node_name}_status", "inprogress")),
                "message": state.get("final_status_message", state.get(f"{node_name}_status_message", "N/A"))
            }
            yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
            time.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")