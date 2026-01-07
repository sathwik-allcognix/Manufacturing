from datetime import date, datetime
from typing import Optional, Dict
from decimal import Decimal

from pydantic import BaseModel, Field


# ============= Organization Schemas =============
class OrganizationBase(BaseModel):
    org_name: str
    industry_type: Optional[str] = None
    address: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    password: str


class OrganizationRead(OrganizationBase):
    org_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Product Schemas =============
class ProductBase(BaseModel):
    product_name: str
    sku: Optional[str] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    org_id: int


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None


class ProductRead(ProductBase):
    product_id: int
    org_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Sales Data Schemas =============
class SalesDataBase(BaseModel):
    sales_date: date
    sales_quantity: float = Field(gt=0, description="Sales quantity must be positive")


class SalesDataCreate(SalesDataBase):
    product_id: int


class SalesUpdate(BaseModel):
    """Schema for updating sales entries - all fields optional"""
    sales_date: Optional[date] = None
    sales_quantity: Optional[float] = Field(None, gt=0, description="Sales quantity must be positive")


class SalesDataRead(SalesDataBase):
    order_id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Legacy aliases for backward compatibility
SalesCreate = SalesDataCreate
SalesRead = SalesDataRead


# ============= Forecast Schemas =============
class ForecastRequest(BaseModel):
    product_id: int
    days: Optional[int] = 30


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
    periods: Optional[int] = None
    granularity: Optional[str] = None  # 'daily', 'monthly', or 'yearly'
    report: Optional[str] = None


# ============= Auth Schemas =============
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    org_id: Optional[int] = None