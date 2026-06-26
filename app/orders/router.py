from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_role
from app.orders.schemas import OrderCreate, OrderResponse, OrderCancelRequest, OrderStatusUpdate
from app.orders import service as order_service


router = APIRouter()

@router.get("/seller", response_model=list[OrderResponse])
def view_seller_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller")),
):
    return order_service.get_seller_orders(db, current_user["sub"])


@router.get("/admin", response_model=list[OrderResponse])
def view_all_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    return order_service.get_all_orders(db)


@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return order_service.create_order(db, data, current_user["sub"])


@router.get("", response_model=list[OrderResponse])
def view_my_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return order_service.get_user_orders(db, current_user["sub"])


@router.get("/{order_id}", response_model=OrderResponse)
def view_single_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return order_service.get_order_by_id(db, order_id, current_user["sub"])


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_my_order(
    order_id: int,
    payload: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return order_service.cancel_order(db, order_id, current_user["sub"], payload.reason)


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller"))
):
    return order_service.update_order_status(db, order_id, payload.new_status, current_user["sub"])