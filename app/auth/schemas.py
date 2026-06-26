from pydantic import BaseModel, EmailStr
from app.users.models import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.customer

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    message: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str