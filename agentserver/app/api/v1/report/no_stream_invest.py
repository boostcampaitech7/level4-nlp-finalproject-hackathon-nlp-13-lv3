import time
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_db, engine
from app.schemas.invest_task import InvestTask, InvestTaskCreate, InvestTaskMinimalResponse
from app.graph import run_graph

router = APIRouter()

def update_task_status(task_id: str, status: str, status_message: str):
    with Session(engine) as db:
        task = db.exec(select(InvestTask).where(InvestTask.task_id == task_id)).first()
        if task:
            task.status = status
            task.status_message = status_message
            db.add(task)
            db.commit()

@router.post("/", response_model=InvestTaskMinimalResponse)
def no_stream_invest_task(
    task_in: InvestTaskCreate,
    db: Session = Depends(get_db)
):
    """
    1) invest_task 레코드 생성
    2) run_graph 동기 실행 -> 각 단계에서 status 업데이트
    3) 최종 완료 후 user_id, task_id, status 반환
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

    # 2. run_graph 실행
    initial_state = {
        "company_name": new_task.company_name,
        "investment_persona": new_task.invest_type
    }
    steps = run_graph(initial_state)

    for node_name, state in steps:
        # 중간 상태 가져오기
        s_msg = state.get(f"{node_name}_status_message", "No message")
        s_val = state.get(f"{node_name}_status", "inprogress")
        # 마지막 노드면 성공 처리
        if node_name == "FinalAnalysisAgent":
            s_val = "success"
            s_msg = "최종 리포트 생성 완료"
        update_task_status(new_task.task_id, s_val, s_msg)

    # 최종 상태 DB 조회
    db.refresh(new_task)
    return InvestTaskMinimalResponse(
        user_id=new_task.user_id,
        task_id=new_task.task_id,
        status=new_task.status
    )