from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"       # 테이블 이름 지정
    __table_args__ = {"schema": "test1"}
    # 테이블에 매핑될 때는 id 필드를 Optional로 하고 기본값을 None으로 설정합니다.
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="사용자의 로그인 이름")
    email: str = Field(..., description="사용자의 이메일 주소")
    password: str = Field(..., description="사용자의 비밀번호")
    is_active: bool = Field(default=True, description="활성 상태 여부")
