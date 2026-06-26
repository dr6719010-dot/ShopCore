from sqlalchemy.orm import Session
from app.cache import redis_client
import json
from app.products.models import Product, Category, Stock, ProductCategory
from app.products.schemas import ProductCreate, ProductUpdate, StockUpdate
from app.products.schemas import ProductResponse, CategoryResponse
from app.products.schemas import ProductResponse
from fastapi import HTTPException, status
from app.users.models import User

CACHE_TTL = 600  # 10 minutes

def invalidate_product_cache(product_id: int = None):
    redis_client.delete("products:all")
    redis_client.delete("categories:all")
    if product_id:
        redis_client.delete(f"products:{product_id}")

def get_all_products(db: Session):
    cache_key = "products:all"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    products = db.query(Product).all()
    serialized = [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]
    redis_client.set(cache_key, json.dumps(serialized), ex=CACHE_TTL)
    return products
    



def create_product(db: Session, data: ProductCreate, seller_email: str):
    # 1. Get seller's integer ID from email
    user = db.query(User).filter(User.email == seller_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # 2. Create product with correct seller_id
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        seller_id=user.id
    )
    db.add(product)
    db.flush()

    # 3. Create stock entry
    stock = Stock(product_id=product.id, quantity=0)
    db.add(stock)

    # 4. Link categories
    for category_id in data.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
        link = ProductCategory(product_id=product.id, category_id=category_id)
        db.add(link)

    db.commit()
    db.refresh(product)
    invalidate_product_cache()
    return product



def get_product_by_id(db: Session, product_id: int):
    cache_key = f"products:{product_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    serialized = ProductResponse.model_validate(product).model_dump(mode="json")
    redis_client.set(cache_key, json.dumps(serialized), ex=CACHE_TTL)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate, seller_email: str):
    user = db.query(User).filter(User.email == seller_email).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your product")
    
    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.price is not None:
        product.price = data.price

    db.commit()
    db.refresh(product)
    invalidate_product_cache(product_id)
    return product


def delete_product(db: Session, product_id: int, seller_email: str):
    user = db.query(User).filter(User.email == seller_email).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your product")
    
    # Delete related records first
    db.query(Stock).filter(Stock.product_id == product_id).delete()
    db.query(ProductCategory).filter(ProductCategory.product_id == product_id).delete()
    
    db.delete(product)
    db.commit()
    invalidate_product_cache(product_id)
    return {"message": "Product deleted successfully"}


def update_stock(db: Session, product_id: int, data: StockUpdate, seller_email: str):
    user = db.query(User).filter(User.email == seller_email).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your product")
    
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock.quantity = data.quantity
    db.commit()
    db.refresh(stock)
    return stock


def get_products_by_category(db: Session, category_id: int):
    cache_key = f"products:category:{category_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    products = db.query(Product).join(ProductCategory).filter(
        ProductCategory.category_id == category_id
    ).all()
    serialized = [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]
    redis_client.set(cache_key, json.dumps(serialized), ex=CACHE_TTL)
    return products


def create_category(db: Session, data):
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    category = Category(name=data.name, description=data.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_all_categories(db: Session):
    cache_key = "categories:all"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    categories = db.query(Category).all()
    serialized = [CategoryResponse.model_validate(c).model_dump(mode="json") for c in categories]
    redis_client.set(cache_key, json.dumps(serialized), ex=CACHE_TTL)
    return categories