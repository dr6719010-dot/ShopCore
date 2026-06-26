from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: float
    created_at: datetime

    class Config:
        from_attributes = True

class OrderDelete(BaseModel):
    order_id: int
    reason: Optional[str] = None


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    new_status: str