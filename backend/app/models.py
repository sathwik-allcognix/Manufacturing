from datetime import datetime, date

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class Organization(Base):
    __tablename__ = "organization"

    org_id = Column(Integer, primary_key=True, index=True)
    org_name = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    industry_type = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "product"

    product_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.org_id"), nullable=False)
    product_name = Column(String, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    organization = relationship("Organization", back_populates="products")
    sales_data = relationship("SalesData", back_populates="product", cascade="all, delete-orphan")


class SalesData(Base):
    __tablename__ = "sales_data"
    __table_args__ = (UniqueConstraint("product_id", "sales_date", name="uix_product_date"),)

    order_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.product_id"), nullable=False)
    sales_date = Column(Date, nullable=False, index=True)
    sales_quantity = Column(Numeric, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="sales_data")


