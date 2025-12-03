from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import  product, sales, forecast, auth
from .configs import config

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Manufacturing Forecasting API",
    version="1.0.0",
)

origins = config.allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(organization.router)
app.include_router(product.router)
app.include_router(sales.router)
app.include_router(forecast.router)
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Manufacturing forecasting backend running"}


