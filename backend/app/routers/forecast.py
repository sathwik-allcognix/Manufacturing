from datetime import date, timedelta
import calendar
import re

from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..agents.forecast_graph import demand_forecast_workflow
from .. import models, schemas
from ..db import get_db
from .auth import get_current_org

router = APIRouter(prefix="/forecast", tags=["forecast"])


# def _parse_nlp_query(text: str) -> tuple[date | None, date | None, int]:
#     """
#     Very lightweight NLP-style parser for forecast requests.
#     Supports phrases like:
#     - "from Jan 2024 to Mar 2024"
#     - "between 2023-01-01 and 2023-06-30"
#     - "for March 2024"
#     - "for 2023"
#     - "next week", "next 2 weeks"
#     - "next month", "next 3 months"
#     - "next 10 days"
#     - "till date" / "till today"
#     """
#     text_l = text.lower()
#     today = date.today()
#     history_start: date | None = None
#     history_end: date | None = None
#     days: int = 30

#     # Horizon parsing
#     m = re.search(r"next\s+(\d+)\s+day", text_l)
#     if m:
#         days = int(m.group(1))
#     else:
#         m = re.search(r"next\s+(\d+)\s+week", text_l)
#         if m:
#             days = int(m.group(1)) * 7
#         elif "next week" in text_l:
#             days = 7
#         else:
#             m = re.search(r"next\s+(\d+)\s+month", text_l)
#             if m:
#                 days = int(m.group(1)) * 30
#             elif "next month" in text_l:
#                 days = 30
#             else:
#                 m = re.search(r"next\s+(\d+)\s+year", text_l)
#                 if m:
#                     days = int(m.group(1)) * 365
#                 elif "next year" in text_l:
#                     days = 365

#     # Date range: "from X to Y" or "between X and Y"
#     m = re.search(r"(from|between)\s+(.+?)\s+(to|and)\s+(.+)", text_l)
#     if m:
#         start_str = m.group(2)
#         end_str = m.group(4)
#         try:
#             history_start = date_parser.parse(start_str, dayfirst=False).date()
#         except Exception:
#             history_start = None
#         try:
#             history_end = date_parser.parse(end_str, dayfirst=False).date()
#         except Exception:
#             history_end = None

#     # "since X" if start still unknown
#     if history_start is None:
#         m = re.search(r"(since|from)\s+([0-9a-zA-Z ,/-]+)", text_l)
#         if m:
#             try:
#                 history_start = date_parser.parse(m.group(2), dayfirst=False).date()
#             except Exception:
#                 history_start = None

#     # Explicit "till date"/"till today"/"until today"
#     if history_end is None and (
#         "till date" in text_l
#         or "till today" in text_l
#         or "until today" in text_l
#         or "up to today" in text_l
#     ):
#         history_end = today

#     # Month + year or year-only if still not set
#     if history_start is None and history_end is None:
#         # Year-only pattern like "2023"
#         m = re.search(r"\b(20[0-9]{2})\b", text_l)
#         if m:
#             y = int(m.group(1))
#             history_start = date(y, 1, 1)
#             history_end = date(y, 12, 31)
#         else:
#             # Try to parse a month+year like "March 2024"
#             try:
#                 dt = date_parser.parse(text_l, default=date(today.year, 1, 1))
#                 history_start = date(dt.year, dt.month, 1)
#                 last_day = calendar.monthrange(dt.year, dt.month)[1]
#                 history_end = date(dt.year, dt.month, last_day)
#             except Exception:
#                 history_start = None
#                 history_end = None

#     return history_start, history_end, days


# @router.get("/{product_id}", response_model=schemas.ForecastResponse)
# def get_forecast(
#     product_id: int,
#     days: int = Query(30, ge=1, le=365),
#     db: Session = Depends(get_db),
#     current_org: models.Organization = Depends(get_current_org),
# ):
#     product = (
#         db.query(models.Product)
#         .filter(models.Product.product_id == product_id)
#         .first()
#     )
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     if product.org_id != current_org.org_id:
#         raise HTTPException(status_code=403, detail="Not authorized to view forecast for this product")

#     initial_state = {
#         "product_id": product_id,
#         "days": days,
#         "time_series": None,
#         "forecast": {},
#         "report": "",
#     }

#     result_state = demand_forecast_workflow.invoke(initial_state)
#     forecast = result_state.get("forecast", {})
#     report = result_state.get("report", "")

#     return schemas.ForecastResponse(
#         product_id=product_id,
#         days=days,
#         forecast=forecast,
#         report=report,
#     )


@router.post("/forecast", response_model=schemas.ChatbotResponse)
def get_forecast_nlp(
    payload: schemas.ForecastNLPRequest,
    db: Session = Depends(get_db),
    current_org: models.Organization = Depends(get_current_org),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.product_id == payload.product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.org_id != current_org.org_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view forecast for this product",
        )

    initial_state = {
        "product_id": payload.product_id,
        "user_query": payload.query,
        "is_forecast_request": False,
        "conversational_response": "",
        "time_series": None,
        "forecast": {},
        "report": "",
        "history_start": None,
        "history_end": None,
    }

    result_state = demand_forecast_workflow.invoke(initial_state)
    
    is_forecast = result_state.get("is_forecast_request", False)
    conversational_response = result_state.get("conversational_response", "")
    forecast = result_state.get("forecast", {})
    report = result_state.get("report", "")
    granularity = result_state.get("granularity", "daily")  # NEW
    
    # Calculate periods based on granularity
    if is_forecast:
        periods = len(forecast)
    else:
        periods = 0

    return schemas.ChatbotResponse(
        product_id=payload.product_id,
        is_forecast_request=is_forecast,
        conversational_response=conversational_response if not is_forecast else None,
        forecast=forecast if is_forecast else None,
        periods=periods if is_forecast else None,  # Changed from 'days'
        granularity=granularity if is_forecast else None,  # NEW
        report=report if is_forecast else None,
    )