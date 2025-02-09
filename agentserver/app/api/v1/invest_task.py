# app/api/v1/invest_task.py
"""
import time
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_db, engine
from app.schemas.invest_task import InvestTask, InvestTaskCreate, InvestTaskDetailedResponse, AgentMessage
from app.graph import run_graph  # run_graph 함수 임포트

router = APIRouter()


@router.post("/invest-task", response_model=InvestTaskDetailedResponse)
def create_invest_task(
    task_in: InvestTaskCreate,
    db: Session = Depends(get_db)
):
    # 1. 클라이언트로부터 전달받은 4개 파라미터로 새 InvestTask 객체 생성 및 DB 저장
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
    
    # 2. invest_task의 초기 상태를 구성 (필요한 경우 추가 정보를 넣을 수 있음)
    initial_state = {
        "user_id": new_task.user_id,
        "invest_type": new_task.invest_type,
        "company_name": new_task.company_name,
        "company_code": new_task.company_code
    }
    
    # 3. run_graph 함수를 동기적으로 호출하여 각 에이전트의 실행 단계별 상태(중간 메시지)를 수집
    #    run_graph는 [(node_name, state), ...] 형태의 리스트를 반환합니다.
    steps = run_graph(initial_state)
    
    # 4. 각 단계에서 해당 에이전트의 상태 메시지를 추출하여 messages 리스트를 구성합니다.
    messages = []
    for node_name, state in steps:
        # 각 에이전트는 자신의 이름을 키로 하여 status_message를 state에 기록했다고 가정합니다.
        msg =f"{node_name}가 작업을 진행중 입니다."
        messages.append(AgentMessage(agent=node_name, message=msg))
    
    # 5. 최종 단계의 상태를 가져옵니다.
    final_state = steps[-1][1] if steps else {}
    final_status = final_state
    
    # 7. 구성된 응답 반환: user_id, task_id, 각 에이전트의 메시지 리스트, 최종 상태
    return InvestTaskDetailedResponse(
        user_id=new_task.user_id,
        task_id=new_task.task_id,
        messages=messages,
        final_status=final_status
    )
"""

# app/api/v1/invest_task.py
import time
import json
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.db.session import get_db, engine
from app.schemas.invest_task import InvestTask, InvestTaskCreate, InvestTaskMinimalResponse
from app.graph import run_graph  # 각 에이전트의 중간 상태를 yield하는 run_graph 함수

router = APIRouter()

def update_task_status(task_id: str, status: str, status_message: str) -> None:

    with Session(engine) as db:
        task = db.exec(select(InvestTask).where(InvestTask.task_id == task_id)).first()
        if task is None:
            print(f"Task {task_id} not found.")
            return
        task.status = status
        task.status_message = status_message
        db.add(task)
        db.commit()

def process_invest_task(task_id: str) -> None:

    
    # 예시: run_graph를 호출한 후 최종 상태로 DB 업데이트
    intermediate_steps = run_graph({})  # 이 함수는 별도로 호출하지 않고, 스트리밍 응답에서 처리할 수도 있습니다.
    if intermediate_steps:
        final_state = intermediate_steps[-1][1]
        final_status = final_state.get("final_report", "unknown")
        final_message = final_state.get("integrated_report", "Final report generated")
        update_task_status(task_id, final_status, final_message)

@router.post("/invest-task-stream", response_model=InvestTaskMinimalResponse)
async def create_invest_task_stream(
    task_in: InvestTaskCreate,
    db: Session = Depends(get_db)
):

    # invest_task 레코드 생성
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
    
    # 초기 상태 구성 (추가 정보가 필요한 경우 여기에 넣습니다)
    initial_state = {
        "user_id": new_task.user_id,
        "invest_type": new_task.invest_type,
        "company_name": new_task.company_name,
        "company_code": new_task.company_code
    }
    
    def event_generator():

        for node_name, state in run_graph(initial_state):
            # 각 에이전트가 작업할 때마다, 해당 에이전트의 상태 메시지와 상태를 추출합니다.
            try:
                message = f"{node_name}가 작업을 진행중 입니다."
                status = "succes"
                event_data = {
                    "agent": node_name,
                    "message": message,
                    "status": status
                }
                yield f"data: {json.dumps(event_data)}\n\n"
            except:
                message = "error"
                status = "failed"
                event_data = {
                    "agent": node_name,
                    "message": message,
                    "status": status
                }
            time.sleep(1)  # 각 단계 사이에 딜레이 (선택 사항)
        
        # 최종 단계 상태 전달 (필요 시)
        final_status = state.get("integrated_report", "unknown")
        event_data = {
            "final_status": final_status,
            "message": state.get("final_report", "Final report generated")
        }
        yield f"data: {json.dumps(event_data)}\n\n"
    
    # StreamingResponse를 반환하면, 클라이언트는 작업 진행 상태를 실시간으로 받을 수 있습니다.
    return StreamingResponse(event_generator(), media_type="text/event-stream")
