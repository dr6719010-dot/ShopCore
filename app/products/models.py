from sqlalchemy import Column, Integer, String, DateTime, Float, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

class ProductCategory(Base):
    __tablename__ = "productcategories"

    __table_args__ = (
    PrimaryKeyConstraint('product_id', 'category_id'),
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)