from pydantic import BaseModel


class TaskCreate(BaseModel):
    user_id: str
    stock_code: str
    investor_type: str


class TaskResponse(BaseModel):

    task_id: str
    message: str
