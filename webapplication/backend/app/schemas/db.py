import uuid
from datetime import datetime

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Identity, UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "users"       # 테이블 이름 지정
    __table_args__ = {"schema": "test1"}
    # 테이블에 매핑될 때는 id 필드를 Optional로 하고 기본값을 None으로 설정합니다.
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="사용자의 로그인 이름")
    email: str = Field(..., description="사용자의 이메일 주소")
    password: str = Field(..., description="사용자의 비밀번호")
    is_active: bool = Field(default=True, description="활성 상태 여부")


class Users(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("uuid", name="users_unique"),
        UniqueConstraint("g_code", name="users_unique_1"),
        {"schema": "auth"},
    )

    # id: 정수형 PK, GENERATED ALWAYS AS IDENTITY로 자동 생성됨
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            Identity(always=True),  # SQL: GENERATED ALWAYS AS IDENTITY
            primary_key=True,
            nullable=False,
        )
    )
    # uuid: PostgreSQL의 UUID 타입 (여기서는 기본값이 지정되지 않았으므로 애플리케이션에서 값을 제공해야 함)
    uuid: str = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), nullable=False)
    )

    # email: NULL 허용
    email: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # last_login_date: timestamptz (시간대 포함) 타입, NULL 허용
    last_login_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    # g_code: NOT NULL, UNIQUE
    g_code: str = Field(
        sa_column=Column(String, nullable=False)
    )


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("task_id", name="tasks_unique"),
        {"schema": "invest"},
    )

    # id: 정수형 기본키, GENERATED ALWAYS AS IDENTITY로 자동 생성
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            Identity(always=True),  # GENERATED ALWAYS AS IDENTITY
            primary_key=True,
            nullable=False,
        )
    )
    # task_id: UUID 타입, UNIQUE 제약 조건
    task_id: str = Field(
        sa_column=Column(UUID(as_uuid=True), nullable=False)
    )
    status: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    report_generate: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    report_summary: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    status_message: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    create_user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), nullable=True)
    )
    kakao_send_status: Optional[bool] = Field(
        default=None,
        sa_column=Column(Boolean, nullable=True)
    )
    kakao_send_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    stock_code: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # "position"은 예약어이므로, 컬럼 이름을 명시적으로 지정합니다.
    stock_position: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    stock_justification: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    modified_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
