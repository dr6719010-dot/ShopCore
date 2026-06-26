import json
import logging
import razorpay
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config import settings
from app.orders.models import Order
from app.payments.models import Payment
from app.users.models import User

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_payment_order(db: Session, order_id: int, user_email: str) -> dict:
    # 1. Get user and order
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied",
        )

    # 2. Validate order status
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not in pending state",
        )

    # 3. Create Razorpay order
    try:
        razorpay_order = razorpay_client.order.create(
            {
                "amount": int(
                    order.total_amount * 100
                ),  # Razorpay uses paise, not rupees
                "currency": "INR",
                "receipt": str(order.id),
            }
        )
    except Exception as e:
        logger.error(f"Razorpay API execution failed for Order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to initiate payment session with gateway",
        )

    # 4. Create Payment record in database
    try:
        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            status="pending",
            payment_gateway_id=razorpay_order["id"],
        )
        db.add(payment)
        db.commit()
    except SQLAlchemyError as db_error:
        db.rollback()
        logger.error(
            f"Database write failed for Payment record on Order {order_id}: {db_error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database operation failed",
        )

    # 5. Return payload to frontend
    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount": order.total_amount,
        "currency": "INR",
    }


def handle_webhook(db: Session, body: bytes, signature: str) -> dict:
    # 1. Verify signature using raw body (do not touch or format the bytes)
    try:
        razorpay_client.utility.verify_webhook_signature(
            body.decode("utf-8"), signature, settings.RAZORPAY_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.warning(f"Webhook signature validation failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    # 2. Parse webhook body safely
    payload = json.loads(body)
    event_type = payload.get("event")

    # Only process target completion events. Ignore intermediate states.
    if event_type not in ["order.paid", "payment.captured"]:
        logger.info(f"Skipping non-completion webhook event: {event_type}")
        return {"status": "skipped", "reason": "event ignored"}

    # Extract payment entity dynamically depending on the event structure
    event_data = payload.get("payload", {})
    
    if "order" in event_data:
        # If 'order.paid' event is active on the dashboard
        payment_entity = event_data["order"]["entity"]
        razorpay_order_id = payment_entity.get("id")
        # For order events, success means the payment condition is fulfilled
        is_success = payment_entity.get("status") == "paid"
    else:
        # Fallback to standard 'payment.captured' payload shape
        payment_entity = event_data.get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        is_success = payment_entity.get("status") == "captured"

    if not razorpay_order_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing razorpay order reference in payload",
        )

    # 3. Find payment record inside an isolated atomic transaction block
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.payment_gateway_id == razorpay_order_id)
            .first()
        )
        if not payment:
            logger.error(
                f"Razorpay order {razorpay_order_id} not mapped in DB"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record tracking code not found",
            )

        # 4. Update payment status
        payment.status = "completed" if is_success else "failed"

        # 5. Update order status conditionally
        if is_success:
            order = db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                order.status = "confirmed"
            else:
                logger.error(
                    f"Orphaned payment ID {payment.id} points to missing Order ID {payment.order_id}"
                )

        # Commit updates as a unified database step
        db.commit()

    except SQLAlchemyError as db_error:
        db.rollback()
        logger.critical(
            f"Database updates crashed handling Razorpay Order ID {razorpay_order_id}: {db_error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Local ledger write error. State changes rolled back.",
        )

    return {"status": "ok"}
