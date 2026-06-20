import enum
from sqlalchemy import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class UserRole(str, enum.Enum):
    customer = "customer"
    seller = "seller"
    admin = "admin"



class User(Base):
    __tablename__ = "users"


    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.customer)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)