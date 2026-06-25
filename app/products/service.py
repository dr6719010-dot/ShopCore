from sqlalchemy.orm import Session
from app.products.models import Product, Category, Stock, ProductCategory
from app.products.schemas import ProductCreate, ProductUpdate, StockUpdate
from fastapi import HTTPException, status
from app.users.models import User

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
    return product


def get_all_products(db: Session):
    return db.query(Product).all()


def get_product_by_id(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
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
    return db.query(Product).join(ProductCategory).filter(
        ProductCategory.category_id == category_id
    ).all()


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
    return db.query(Category).all()