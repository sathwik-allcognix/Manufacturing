from pydantic import BaseModel, Field
from typing import Optional, Literal

class QueryClassification(BaseModel):
    is_forecast_request: bool = Field(
        description="True if user wants a forecast, False otherwise"
    )

class ForecastParams(BaseModel):
    start_horizon: int = Field(
        description="Days from last_date to start of forecast period"
    )
    end_horizon: int = Field(
        description="Days from last_date to end of forecast period"
    )
    single_day: bool = Field(
        description="True if forecasting a single specific day"
    )
    granularity: Literal["daily", "monthly", "yearly"] = Field(
        default="daily",
        description=(
            "Forecast granularity: 'daily' for day-by-day, "
            "'monthly' for month-by-month, 'yearly' for year-by-year"
        )
    )
    history_start: Optional[str] = Field(
        default=None,
        description="ISO format date string for history start (YYYY-MM-DD)"
    )
    history_end: Optional[str] = Field(
        default=None,
        description="ISO format date string for history end (YYYY-MM-DD)"
    )