from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from .auth import get_current_org

router = APIRouter(prefix="/product", tags=["product"])


@router.post("", response_model=schemas.ProductRead)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    if current_org.org_id != product_in.org_id:
        raise HTTPException(status_code=403, detail="Not authorized to create product for this organization")

    product = models.Product(
        org_id=product_in.org_id,
        product_name=product_in.product_name,
        sku=product_in.sku,
        description=product_in.description,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/by_org/{org_id}", response_model=List[schemas.ProductRead])
def list_products_by_org(
    org_id: int,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    if current_org.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to view products for this organization")
    products = db.query(models.Product).filter(models.Product.org_id == org_id).all()
    return products


