from fastapi import FastAPI

app = FastAPI(title="ShopCore:")

@app.get("/", tags=["Home"])
def home():
    """Welcome Endpoint"""
    return {"message": "Welcome to ShopCore"}