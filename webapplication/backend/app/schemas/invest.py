from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone, timedelta

gmt9 = timezone(timedelta(hours=9))


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


class ReportLog(BaseModel):
    task_id: str
    status: str
    status_message: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    investor_type: Optional[str] = None
    stock_position: Optional[str] = None
    stock_justification: Optional[str] = None
    report_generate: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.astimezone(
                gmt9).isoformat() if dt else None
        }


class ReportLogsResponse(BaseModel):
    report_logs: list[ReportLog]
