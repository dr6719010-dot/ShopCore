import bcrypt
from app.users.models import User
from sqlalchemy.orm import Session
from app.auth.jwt import create_token
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