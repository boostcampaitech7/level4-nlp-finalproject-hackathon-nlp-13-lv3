from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class TaskCreate(BaseModel):
    user_id: str
    stock_code: str
    investor_type: str


class TaskResponse(BaseModel):
    task_id: str
    message: str


class ReportRequest(BaseModel):
    task_id: str
    user_id: str


class ReportResponse(BaseModel):
    task_id: str
    text: Optional[str] = None
    status: str
    status_message: Optional[str] = None
