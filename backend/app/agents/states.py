from typing import TypedDict, Optional, Literal, Dict
from datetime import date
import pandas as pd


class ForecastState(TypedDict, total=False):
    product_id: int
    user_query: str
    is_forecast_request: bool
    conversational_response: str
    start_horizon: int
    end_horizon: int
    single_day: bool
    granularity: Literal["daily", "monthly", "yearly"]
    time_series: pd.DataFrame
    forecast: Dict[str, float]
    report: str
    history_start: Optional[date]
    history_end: Optional[date]
    last_date: Optional[date]
    _target_year: Optional[int]  # For monthly/yearly forecasts
