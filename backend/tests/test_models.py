from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app import models


def test_orm_relationships():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        org = models.Organization(org_name="Test Org")
        db.add(org)
        db.commit()
        db.refresh(org)

        product = models.Product(org_id=org.org_id, product_name="Widget")
        db.add(product)
        db.commit()
        db.refresh(product)

        # Relationship: org.products
        assert len(org.products) == 1
        assert org.products[0].product_id == product.product_id

        # Relationship: product.organization
        assert product.organization.org_id == org.org_id

        sales = models.SalesData(
            product_id=product.product_id,
            sales_date="2024-01-01",
            sales_quantity=10,
        )
        db.add(sales)
        db.commit()
        db.refresh(sales)

        assert len(product.sales_data) == 1
        assert product.sales_data[0].order_id == sales.order_id
    finally:
        db.close()


