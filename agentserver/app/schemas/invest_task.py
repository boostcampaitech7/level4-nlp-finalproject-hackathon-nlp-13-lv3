from sqlmodel import SQLModel, Field
import uuid
from pydantic import BaseModel

class InvestTask(SQLModel, table=True):
    """
    invest_task 테이블
    - user_id, invest_type, company_name, company_code (4개 파라미터)
    - task_id(UUID), status, status_message
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    invest_type: str
    company_name: str
    company_code: str
    status: str = Field(default="inprogress")
    status_message: str = Field(default="Task created, waiting to start.")

class InvestTaskCreate(SQLModel):
    """
    요청 바디 (4개 파라미터)
    """
    user_id: str
    invest_type: str
    company_name: str
    company_code: str

class InvestTaskMinimalResponse(BaseModel):
    """
    응답 바디 (user_id, task_id, status)
    """
    user_id: str
    task_id: str
    status: str