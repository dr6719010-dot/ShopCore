from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.auth.schemas import RegisterRequest, LoginRequest
from app.auth.service import register_user, login_user
router = APIRouter()

@router.post("/register")
def register(data:RegisterRequest ,db: Session = Depends(get_db)):
    return register_user(db, data)

@router.post("/login")
def login(data:LoginRequest ,db: Session = Depends(get_db)):
    return login_user(db, data)