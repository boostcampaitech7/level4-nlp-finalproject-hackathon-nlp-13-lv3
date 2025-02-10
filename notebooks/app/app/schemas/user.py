from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserResponse(BaseModel):

    name: str
    email: str
    id: int

    class Config:
        orm_mode = True
