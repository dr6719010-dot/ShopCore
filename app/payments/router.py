from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.payments import service as payment_service

router = APIRouter()

@router.post("/{order_id}")
def create_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return payment_service.create_payment_order(db, order_id, current_user["sub"])

@router.post("/webhook")
async def webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    return payment_service.handle_webhook(db, body, signature)