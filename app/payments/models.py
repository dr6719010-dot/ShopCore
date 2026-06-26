import enum
from sqlalchemy import Enum
from sqlalchemy import Column, Integer, String, DateTime, Float, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy import Numeric
from sqlalchemy import ForeignKey
from app.database import Base

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    payment_gateway_id = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())