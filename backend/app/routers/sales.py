from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from .auth import get_current_org

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=schemas.SalesRead)
def create_sales_entry(
    sales_in: schemas.SalesCreate,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == sales_in.product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=400, detail="Product does not exist")

    if product.org_id != current_org.org_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to add sales for this product",
        )

    # Enforce unique (product_id, sales_date)
    existing = (
        db.query(models.SalesData)
        .filter(
            models.SalesData.product_id == sales_in.product_id,
            models.SalesData.sales_date == sales_in.sales_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Sales entry for this product and date already exists",
        )

    sales = models.SalesData(
        product_id=sales_in.product_id,
        sales_date=sales_in.sales_date,
        sales_quantity=sales_in.sales_quantity,
    )
    db.add(sales)
    db.commit()
    db.refresh(sales)
    return sales


@router.get("/by_product/{product_id}", response_model=List[schemas.SalesRead])
def list_sales_by_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.org_id != current_org.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to view sales for this product")

    sales = (
        db.query(models.SalesData)
        .filter(models.SalesData.product_id == product_id)
        .order_by(models.SalesData.sales_date.desc())
        .all()
    )
    return sales


@router.get("/by_org/{org_id}", response_model=List[schemas.SalesRead])
def list_sales_by_org(
    org_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    if current_org.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to view sales for this organization")

    sales = (
        db.query(models.SalesData)
        .join(models.Product, models.Product.product_id == models.SalesData.product_id)
        .filter(models.Product.org_id == org_id)
        .order_by(models.SalesData.sales_date.desc())
        .all()
    )
    return sales


@router.get("/{order_id}", response_model=schemas.SalesRead)
def get_sales_entry(
    order_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    sales = (
        db.query(models.SalesData)
        .filter(models.SalesData.order_id == order_id)
        .first()
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales entry not found")
    
    # Check authorization
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == sales.product_id)
        .first()
    )
    if product.org_id != current_org.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this sales entry")
    
    return sales


@router.put("/{order_id}", response_model=schemas.SalesRead)
def update_sales_entry(
    order_id: int,
    sales_update: schemas.SalesUpdate,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    sales = (
        db.query(models.SalesData)
        .filter(models.SalesData.order_id == order_id)
        .first()
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales entry not found")
    
    # Check authorization
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == sales.product_id)
        .first()
    )
    if product.org_id != current_org.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this sales entry")
    
    # Check if updating date would create duplicate
    if sales_update.sales_date and sales_update.sales_date != sales.sales_date:
        existing = (
            db.query(models.SalesData)
            .filter(
                models.SalesData.product_id == sales.product_id,
                models.SalesData.sales_date == sales_update.sales_date,
                models.SalesData.order_id != order_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Sales entry for this product and date already exists",
            )
    
    # Update fields
    if sales_update.sales_date is not None:
        sales.sales_date = sales_update.sales_date
    if sales_update.sales_quantity is not None:
        sales.sales_quantity = sales_update.sales_quantity
    
    db.commit()
    db.refresh(sales)
    return sales


@router.delete("/{order_id}")
def delete_sales_entry(
    order_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    sales = (
        db.query(models.SalesData)
        .filter(models.SalesData.order_id == order_id)
        .first()
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales entry not found")
    
    # Check authorization
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == sales.product_id)
        .first()
    )
    if product.org_id != current_org.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this sales entry")
    
    db.delete(sales)
    db.commit()
    return {"message": "Sales entry deleted successfully"}