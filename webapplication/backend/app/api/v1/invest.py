from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.invest import TaskCreate, TaskResponse, ReportRequest, ReportResponse

from app.db.session import get_db
from app.schemas.db import Task, Stock
from fastapi import Query
import uuid
from uuid import UUID

router = APIRouter()


@router.put("/", response_model=TaskResponse)
async def create_a_report_task(report_request: TaskCreate, db: Session = Depends(get_db)):
    # 예시: 필드 검증 및 메시지 리턴
    if not report_request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not report_request.stock_code:
        raise HTTPException(status_code=400, detail="stock_code is required")
    if not report_request.investor_type:
        raise HTTPException(
            status_code=400, detail="investor_type is required")
    now = datetime.now(ZoneInfo("Asia/Seoul"))

    stock = db.query(Stock).filter(Stock.stock_code ==
                                   report_request.stock_code).first()
    stock_name = stock.stock_name if stock else None

    task = Task(task_id=uuid.uuid4(), create_user_id=report_request.user_id, investor_type=report_request.investor_type,
                stock_code=report_request.stock_code, stock_name=stock_name, created_at=now, status="시작 전")
    db.add(task)
    db.commit()
    db.refresh(task)
    print(f"Task created: {task.task_id}")
    return TaskResponse(task_id=str(task.task_id), message=f"generating report (id = {task.task_id})")


@router.get("/report", response_model=ReportResponse)
async def get_a_report(task_id: UUID = Query(...), user_id: UUID = Query(...), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id,
                                 Task.create_user_id == user_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return ReportResponse(task_id=str(task.task_id), status=task.status, status_message=task.status_message, text=task.report_generate)
