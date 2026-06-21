from sqlalchemy.orm import Session
from app.database import SessionLocal
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from app.auth.jwt import verify_token
from app.cache import is_token_blacklisted


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    payload = verify_token(token)
    return payload

def require_role(role: str):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user["role"] != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        return current_user
    return role_checker