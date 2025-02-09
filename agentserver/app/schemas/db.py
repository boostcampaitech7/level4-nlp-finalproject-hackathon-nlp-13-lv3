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


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("task_id", name="tasks_unique"),
        {"schema": "invest"},
    )

    # id: 정수형 기본키, GENERATED ALWAYS AS IDENTITY
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            Identity(always=True),
            primary_key=True,
            nullable=False,
        )
    )
    # task_id: UUID, NOT NULL, UNIQUE 제약조건은 __table_args__에 정의됨
    task_id: str = Field(
        sa_column=Column(UUID(as_uuid=True), nullable=False)
    )
    # status: 상태 정보를 나타내는 문자열 (NULL 허용)
    status: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # report_generate: 리포트 생성 관련 문자열 (NULL 허용)
    report_generate: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # report_summary: 리포트 요약 관련 문자열 (NULL 허용)
    report_summary: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # created_at: 생성 시각, timestamptz 타입 (NULL 허용)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    # status_message: 상태 메시지 (NULL 허용)
    status_message: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # create_user_id: 생성 사용자 UUID (NULL 허용)
    create_user_id: Optional[str] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), nullable=True)
    )
    # kakao_send_status: 카카오 전송 상태 (Boolean, NULL 허용)
    kakao_send_status: Optional[bool] = Field(
        default=None,
        sa_column=Column(Boolean, nullable=True)
    )
    # kakao_send_at: 카카오 전송 시각, timestamptz (NULL 허용)
    kakao_send_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    # stock_code: 주식 종목 코드 (varchar, NULL 허용)
    stock_code: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # stock_position: 주식 포지션 (varchar, NULL 허용)
    stock_position: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # stock_justification: 주식 투자 근거 (varchar, NULL 허용)
    stock_justification: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # modified_at: 수정 시각, timestamptz (NULL 허용)
    modified_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    # investor_type: 투자자 유형 (varchar, NULL 허용)
    investor_type: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # stock_name: 기업명 (varchar, NULL 허용)
    stock_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )


class Stock(SQLModel, table=True):
    __tablename__ = "stocks"
    __table_args__ = (
        UniqueConstraint("stock_code", name="stocks_unique"),
        {"schema": "invest"},
    )

    # id: 정수형 기본키, GENERATED ALWAYS AS IDENTITY
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            Identity(always=True),  # 자동 증가 설정
            primary_key=True,
            nullable=False,
        )
    )
    # stock_name: NULL 허용
    stock_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True)
    )
    # stock_code: NOT NULL, UNIQUE 제약 조건이 있음 (UniqueConstraint를 __table_args__에 지정)
    stock_code: str = Field(
        sa_column=Column(String, nullable=False)
    )
