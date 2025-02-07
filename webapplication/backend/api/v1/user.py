from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.schemas.db import User

from app.db.session import get_db
from starlette.requests import Request

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, request_obj: Request, db: Session = Depends(get_db)):
    logger = request_obj.state.logger
    db_user = User(name=user.name, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, request_obj: Request, db: Session = Depends(get_db)):
    logger = request_obj.state.logger
    db_user = db.query(User).filter(User.id == user_id).first()
    logger.info(f"User ID: {user_id}")
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, request_obj: Request, db: Session = Depends(get_db)):
    logger = request_obj.state.logger
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, request_obj: Request, user: UserCreate, db: Session = Depends(get_db)):
    logger = request_obj.state.logger
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user
