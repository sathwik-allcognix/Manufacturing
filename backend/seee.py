# # backend/seed_demo_data_org2.py

# from datetime import date, timedelta

# from app.db import SessionLocal, Base, engine
# from app import models


# def main():
#     # Make sure tables exist
#     Base.metadata.create_all(bind=engine)

#     db = SessionLocal()
#     try:
#         # =========================================
#         # 1) Use EXISTING org with org_id = 2
#         # =========================================
#         org = db.query(models.Organization).filter(models.Organization.org_id == 2).first()
#         if org is None:
#             raise ValueError("Organization with org_id = 2 does not exist. Please create it first.")

#         print(f"Using existing organization org_id={org.org_id}, name={org.org_name}")

#         # =========================================
#         # 2) Create / locate products under org 2
#         #    SKUs must be globally unique -> append org_id
#         # =========================================

#         # Product A
#         product_a = (
#             db.query(models.Product)
#             .filter(models.Product.org_id == org.org_id,
#                     models.Product.product_name == "Seeded Widget A")
#             .first()
#         )
#         if product_a is None:
#             product_a = models.Product(
#                 org_id=org.org_id,
#                 product_name="Seeded Widget A",
#                 sku=f"SEED-A-{org.org_id}",  # UNIQUE globally
#                 description="Seeded product A for org 2",
#             )
#             db.add(product_a)
#             db.commit()
#             db.refresh(product_a)

#         # Product B
#         product_b = (
#             db.query(models.Product)
#             .filter(models.Product.org_id == org.org_id,
#                     models.Product.product_name == "Seeded Widget B")
#             .first()
#         )
#         if product_b is None:
#             product_b = models.Product(
#                 org_id=org.org_id,
#                 product_name="Seeded Widget B",
#                 sku=f"SEED-B-{org.org_id}",  # UNIQUE globally
#                 description="Seeded product B for org 2",
#             )
#             db.add(product_b)
#             db.commit()
#             db.refresh(product_b)

#         print(f"Products in org 2: {product_a.product_id} (A), {product_b.product_id} (B)")

#         # =========================================
#         # 3) Seed LAST 3 YEARS of daily sales data
#         # =========================================

#         start = date.today() - timedelta(days=365 * 3)
#         total_days = 365 * 3

#         for i in range(total_days):
#             d = start + timedelta(days=i)

#             # Product A: slow long-term increasing trend
#             qty_a = 10 + int(i * 0.01)  # increases ~10 units per year

#             existing_a = (
#                 db.query(models.SalesData)
#                 .filter(
#                     models.SalesData.product_id == product_a.product_id,
#                     models.SalesData.sales_date == d,
#                 )
#                 .first()
#             )
#             if not existing_a:
#                 db.add(
#                     models.SalesData(
#                         product_id=product_a.product_id,
#                         sales_date=d,
#                         sales_quantity=qty_a,
#                     )
#                 )

#             # Product B: fluctuating noise around 20
#             fluctuation = ((i % 7) - 3)  # nice periodic wave
#             qty_b = 20 + fluctuation

#             existing_b = (
#                 db.query(models.SalesData)
#                 .filter(
#                     models.SalesData.product_id == product_b.product_id,
#                     models.SalesData.sales_date == d,
#                 )
#                 .first()
#             )
#             if not existing_b:
#                 db.add(
#                     models.SalesData(
#                         product_id=product_b.product_id,
#                         sales_date=d,
#                         sales_quantity=qty_b,
#                     )
#                 )

#         db.commit()
#         print(f"✔️ Seeded daily sales data for org_id=2 for last 3 years ({total_days} days).")

#     finally:
#         db.close()


# if __name__ == "__main__":
#     main()


from datetime import date
from app.db import SessionLocal, Base, engine
from app import models


def main():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # =========================================
        # Delete sales records in YEAR 2026
        # =========================================

        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)

        # Query records first (optional, just to show count)
        to_delete = (
            db.query(models.SalesData)
            .filter(
                models.SalesData.sales_date >= start_date,
                models.SalesData.sales_date <= end_date
            )
        )

        count = to_delete.count()

        if count == 0:
            print("ℹ️ No sales data found for the year 2026.")
        else:
            print(f"⚠️ Found {count} sales rows in 2026. Deleting...")

            to_delete.delete(synchronize_session=False)
            db.commit()

            print(f"✔️ Deleted {count} sales data rows for year 2026.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
