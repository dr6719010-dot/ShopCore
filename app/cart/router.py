from pydantic import BaseModel
from app.cache import redis_client
from fastapi import HTTPException
from app.dependencies import get_current_user
from fastapi import APIRouter, Depends, status
import json

class CartItem(BaseModel):
    product_id: int
    quantity: int

class UpdateCartItem(BaseModel):
    quantity: int


CART_TTL = 7*24*60*60

router = APIRouter()

@router.get("", response_model=list[CartItem])
def view_my_cart(
    current_user: dict = Depends(get_current_user),
):
    cart_key = f"cart:{current_user['sub']}"
    data = redis_client.get(cart_key)
    if not data:
        return []
    cart_data = json.loads(data)
    return cart_data

@router.post("", response_model=list[CartItem])
def add_to_my_cart(
    item_input: CartItem,
    current_user: dict = Depends(get_current_user),
):
    cart_key = f"cart:{current_user['sub']}"
    raw_data = redis_client.get(cart_key)
    cart = json.loads(raw_data) if raw_data else []
    product_exists = False
    for item in cart:
        if item.get("product_id") == item_input.product_id:
            item["quantity"] += item_input.quantity
            product_exists = True
            break

    if not product_exists:
        cart.append({
            "product_id": item_input.product_id, 
            "quantity": item_input.quantity
        })

    redis_client.set(cart_key, json.dumps(cart), ex=CART_TTL)
    return cart

@router.put("/{product_id}")
def update_cart_item(
    product_id: int,
    data: UpdateCartItem,
    current_user: dict = Depends(get_current_user),
):
    cart_key = f"cart:{current_user['sub']}"
    raw_data = redis_client.get(cart_key)
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Cart is empty"
        )
    cart = json.loads(raw_data)
    product_found = False
    for item in cart:
        if item.get("product_id") == product_id:
            item["quantity"] = data.quantity
            product_found = True
            break

    if not product_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not in cart"
        )
    redis_client.set(cart_key, json.dumps(cart), ex=CART_TTL)
    return cart

@router.delete("/{product_id}", response_model=list[CartItem])
def remove_cart_item(
    product_id: int,  
    current_user: dict = Depends(get_current_user),
):
    cart_key = f"cart:{current_user['sub']}"
    raw_data = redis_client.get(cart_key)
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Cart is empty"
        )
        
    cart = json.loads(raw_data)
    initial_length = len(cart)
    updated_cart = [
        item for item in cart 
        if item.get("product_id") != product_id
    ]
    
    if len(updated_cart) == initial_length:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not in cart"
        )
        
    redis_client.set(cart_key, json.dumps(updated_cart), ex=CART_TTL)
    return updated_cart


@router.delete("")
def clear_cart(
    current_user: dict = Depends(get_current_user),
):
    cart_key = f"cart:{current_user['sub']}"
    redis_client.delete(cart_key)
    return {"message": "Cart cleared successfully"}