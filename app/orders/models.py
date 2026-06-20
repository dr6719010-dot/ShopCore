import enum
from sqlalchemy import Enum
from sqlalchemy import Column, Integer, String, DateTime, Float, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from app.database import Base

class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"



class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())



class OrderItem(Base):
    __tablename__ = "orderitems"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)