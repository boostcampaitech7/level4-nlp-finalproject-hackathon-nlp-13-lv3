# app/api/v1/endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.example import ExampleRequest, ExampleResponse

from app.db.session import get_db

router = APIRouter()


@router.get("/", response_model=ExampleResponse)
def get_example(db: Session = Depends(get_db)):
    # 예시: 단순 메시지 리턴 (실제 DB 쿼리는 필요에 따라 구현)
    return ExampleResponse(message="This is a GET example endpoint")


@router.post("/", response_model=ExampleResponse)
def create_example(example: ExampleRequest, db: Session = Depends(get_db)):
    # 예시: 필드 검증 및 메시지 리턴
    if not example.name:
        raise HTTPException(status_code=400, detail="Name field is required")
    return ExampleResponse(message=f"Hello, {example.name}!")


@router.put("/", response_model=ExampleResponse)
def update_example(example: ExampleRequest, db: Session = Depends(get_db)):
    # 예시: 필드 검증 및 메시지 리턴
    if not example.name:
        raise HTTPException(status_code=400, detail="Name field is required")
    return ExampleResponse(message=f"Updated name to {example.name}")


@router.delete("/", response_model=ExampleResponse)
def delete_example(db: Session = Depends(get_db)):
    # 예시: 단순 메시지 리턴 (실제 DB 쿼리는 필요에 따라 구현)
    return ExampleResponse(message="This is a DELETE example endpoint")

# session으로 불러와서 SQLModel도 불러온뒤 postgresql로 연결하고 name, id, email을 만들어서 사용자 정보를 저장하는 예시 api를 만들어보자
