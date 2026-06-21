import bcrypt
from app.users.models import User
from sqlalchemy.orm import Session
from app.auth.jwt import create_token, verify_token
from app.cache import blacklist_token
from datetime import datetime, timezone
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from fastapi import HTTPException, status


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    # Convert both strings to bytes to perform the check
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def register_user(db: Session, data: RegisterRequest):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    get_hashed_password = hash_password(data.password)
    new_user = User(email=data.email, password_hash=get_hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}
    

def login_user(db:Session, data: LoginRequest):
    verify_user = db.query(User).filter(User.email == data.email).first()
    if not verify_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Password or Username"
        )
    
    verifying_password = verify_password(data.password, verify_user.password_hash)
    if not verifying_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Password or Username"
        )
    
    token_payload = {
        "sub": verify_user.email,
        "role": verify_user.role
        }
    token = create_token(data=token_payload)

    return TokenResponse(access_token=token, token_type="bearer")


def logout_user(token: str):
    try:
        payload = verify_token(token)
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Token payload is missing expiration metadata"
            )
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        expiry_seconds = exp_timestamp - current_timestamp
        blacklist_token(token, expiry_seconds)
        return {"message": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or already expired token"
        )