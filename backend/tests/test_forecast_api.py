import os

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app  # noqa: E402
from app.db import Base, engine, SessionLocal  # noqa: E402
from app import models  # noqa: E402


client = TestClient(app)


def setup_module(_module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
      org = models.Organization(org_name="API Org")
      db.add(org)
      db.commit()
      db.refresh(org)

      product = models.Product(org_id=org.org_id, product_name="API Product")
      db.add(product)
      db.commit()
      db.refresh(product)

      # Add a few days of sales so ARIMA has data
      for day in range(1, 6):
          sales = models.SalesData(
              product_id=product.product_id,
              sales_date=f"2024-01-0{day}",
              sales_quantity=10 + day,
          )
          db.add(sales)
      db.commit()
      _module.product_id = product.product_id
    finally:
      db.close()


def test_forecast_endpoint():
    # Use the product created in setup_module
    product_id = globals().get("product_id", 1)
    response = client.get(f"/forecast/{product_id}", params={"days": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id
    assert data["days"] == 5
    assert isinstance(data["forecast"], dict)
    assert "report" in data


