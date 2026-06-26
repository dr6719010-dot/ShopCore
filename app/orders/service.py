import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.orders.models import Order, OrderItem
from app.orders.schemas import OrderCreate
from app.users.models import User
from app.products.models import Product  
from app.products.models import Stock      

logger = logging.getLogger(__name__)

def create_order(db: Session, data: OrderCreate, user_email: str):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    order_items = []
    total = 0.00

    sorted_items = sorted(data.items, key=lambda x: x.product_id)

    try:
        for item in sorted_items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity for product ID {item.product_id} must be greater than zero."
                )

            # Query the product
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} does not exist."
                )

            # Lock the stock row with .with_for_update()
            stock = db.execute(
                select(Stock)
                .where(Stock.product_id == item.product_id)
                .with_for_update()
            ).scalar_one_or_none()

            if not stock:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock not found for product {item.product_id}"
                )

            # Check if enough stock exists
            if stock.quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {item.product_id}"
                )

            # Decrement stock
            stock.quantity -= item.quantity

            # Create OrderItem
            order_item = OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                price_at_purchase=product.price
            )

            # Add to order_items list
            order_items.append(order_item)

            # Add to total
            total += float(product.price) * item.quantity

        # Create Order (without items column)
        new_order = Order(
            user_id=user.id,
            total_amount=total
        )

        # Add order and flush to populate id field
        db.add(new_order)
        db.flush()

        # Link order items to the generated order id
        for order_item in order_items:
            order_item.order_id = new_order.id

        # Add everything to the session
        db.add_all(order_items)

        # Commit everything together
        db.commit()
        db.refresh(new_order)
        return new_order

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during order transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while processing your order transaction."
        )
    
def _get_user_by_email(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


def get_user_orders(db: Session, user_email: str) -> list[Order]:
    user = _get_user_by_email(db, user_email)
    return db.query(Order).filter(Order.user_id == user.id).all()

def get_order_by_id(db: Session, order_id: int, user_email: str) -> Order:
    user = _get_user_by_email(db, user_email)
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )
    return order


def cancel_order(db: Session, order_id: int, user_email: str, reason: str) -> Order:
    user = _get_user_by_email(db, user_email)
    
    try:
        # Lock the order row immediately — this is the fix
        order = db.execute(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user.id)
            .with_for_update()
        ).scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found."
            )

        if order.status in ["cancelled", "shipped", "delivered"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be cancelled because its current status is '{order.status}'."
            )

        order.status = "cancelled"
        order.cancel_reason = reason

        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

        for item in order_items:
            stock = db.execute(
                select(Stock)
                .where(Stock.product_id == item.product_id)
                .with_for_update()
            ).scalar_one_or_none()

            if stock:
                stock.quantity += item.quantity
            else:
                logger.warning(f"Stock row missing for product ID {item.product_id} during cancel order.")

        db.commit()
        db.refresh(order)
        return order

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error while cancelling order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while cancelling your order."
        )
    

def get_seller_orders(db: Session, seller_email: str) -> list[Order]:
    seller = _get_user_by_email(db, seller_email)
    

    return db.query(Order)\
        .join(OrderItem, OrderItem.order_id == Order.id)\
        .join(Product, Product.id == OrderItem.product_id)\
        .filter(Product.seller_id == seller.id)\
        .distinct()\
        .all()

def get_all_orders(db: Session) -> list[Order]:
    return db.query(Order).all()


def update_order_status(db: Session, order_id: int, new_status: str, seller_email: str) -> Order:
    seller = _get_user_by_email(db, seller_email)
    
    allowed_statuses = ["shipped", "delivered"]
    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {allowed_statuses}"
        )
    try:
        order = db.query(Order)\
            .join(OrderItem, OrderItem.order_id == Order.id)\
            .join(Product, Product.id == OrderItem.product_id)\
            .filter(Order.id == order_id, Product.seller_id == seller.id)\
            .first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or you do not have permission to modify it."
            )

        order.status = new_status
        db.commit()
        db.refresh(order)
        return order

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating status for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while modifying the order status."
        )