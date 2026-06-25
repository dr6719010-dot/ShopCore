from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, require_role
from app.products import service
from app.products.schemas import (
    ProductCreate, ProductUpdate, StockUpdate,
    ProductResponse, CategoryCreate, CategoryResponse
)

router = APIRouter()

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    return service.create_category(db, data)

@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return service.get_all_categories(db)

@router.post("/", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller"))
):
    return service.create_product(db, data, seller_email=current_user["sub"])

@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return service.get_all_products(db)

@router.get("/category/{category_id}", response_model=list[ProductResponse])
def get_by_category(category_id: int, db: Session = Depends(get_db)):
    return service.get_products_by_category(db, category_id)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return service.get_product_by_id(db, product_id)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller"))
):
    return service.update_product(db, product_id, data, seller_email=current_user["sub"])

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller"))
):
    return service.delete_product(db, product_id, seller_email=current_user["sub"])

@router.post("/{product_id}/stock")
def update_stock(
    product_id: int,
    data: StockUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("seller"))
):
    return service.update_stock(db, product_id, data, seller_email=current_user["sub"])