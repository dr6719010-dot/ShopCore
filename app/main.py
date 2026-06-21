from fastapi import FastAPI
from app.auth.router import router

app = FastAPI(title="ShopCore:")

@app.get("/", tags=["Home"])
def home():
    """Welcome Endpoint"""
    return {"message": "Welcome to ShopCore"}


app.include_router(router, prefix="/auth", tags=["auth"])