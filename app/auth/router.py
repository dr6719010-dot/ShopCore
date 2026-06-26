from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.auth.schemas import RegisterRequest, LoginRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.service import register_user, login_user, logout_user, refresh_access_token

router = APIRouter()
security = HTTPBearer()

@router.post("/register")
def register(data:RegisterRequest ,db: Session = Depends(get_db)):
    return register_user(db, data)

@router.post("/login")
def login(data:LoginRequest ,db: Session = Depends(get_db)):
    return login_user(db, data)

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return logout_user(token)

@router.post("/refresh")
def refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return refresh_access_token(credentials.credentials)