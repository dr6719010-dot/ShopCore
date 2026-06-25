from fastapi import FastAPI, Depends
from app.auth.router import router
from app.dependencies import get_current_user, require_role
from app.products.router import router as products_router

app = FastAPI(title="ShopCore:")

@app.get("/", tags=["Home"])
def home():
    """Welcome Endpoint"""
    return {"message": "Welcome to ShopCore"}


app.include_router(router, prefix="/auth", tags=["auth"])


app.include_router(products_router, prefix="/products", tags=["products"])