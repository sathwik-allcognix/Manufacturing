from datetime import date, datetime
from typing import Optional, Dict

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    org_name: str
    industry_type: Optional[str] = None
    address: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    # Only used for input; not returned in responses
    password: str


class OrganizationRead(OrganizationBase):
    org_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    org_id: int
    product_name: str
    sku: Optional[str] = None
    description: Optional[str] = None


class ProductRead(ProductCreate):
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesCreate(BaseModel):
    product_id: int
    sales_date: date
    sales_quantity: float


class SalesRead(SalesCreate):
    order_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastResponse(BaseModel):
    product_id: int
    days: int
    forecast: Dict[str, float]
    report: str


class ForecastNLPRequest(BaseModel):
    product_id: int
    query: str


class ChatbotResponse(BaseModel):
    product_id: int
    is_forecast_request: bool
    conversational_response: Optional[str] = None
    forecast: Optional[Dict[str, float]] = None
    periods: Optional[int] = None  # Changed from 'days'
    granularity: Optional[str] = None  # NEW: 'daily', 'monthly', or 'yearly'
    report: Optional[str] = None


