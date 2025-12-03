from typing import Dict, TypedDict, Any, Optional, Literal
from datetime import timedelta, date
import json
import warnings
import logging
import pandas as pd
import numpy as np
from langchain_core.prompts import ChatPromptTemplate

from pmdarima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from langgraph.graph import StateGraph, END

from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import SalesData
from .tools import get_llm

from langchain_core.output_parsers import PydanticOutputParser
from .models import QueryClassification, ForecastParams
from .prompts import fotecasting_extract_params_prompt, fotecasting_classify_query_prompt
from .states import ForecastState
classification_parser = PydanticOutputParser(pydantic_object=QueryClassification)
params_parser = PydanticOutputParser(pydantic_object=ForecastParams)


logger = logging.getLogger("forecast_workflow")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)



def classify_query_agent(state: ForecastState) -> ForecastState:
    llm = get_llm()
    user_query = state.get("user_query", "")
    
    parser = classification_parser

    prompt = fotecasting_classify_query_prompt

    formatted = prompt.format(
        format_instructions=parser.get_format_instructions(),
        user_query=user_query
    )

    response = llm.invoke(formatted)
    parsed = parser.parse(response.content)

    return {
        "is_forecast_request": parsed.is_forecast_request,
    }


def conversational_response_agent(state: ForecastState) -> ForecastState:
    logger.info("[conversational_response_agent] Generating conversational response")

    llm = get_llm()
    user_query = state.get("user_query", "")

    prompt = fotecasting_conversational_response_prompt

    formatted = prompt.format(user_query=user_query)
    resp = llm.invoke(formatted)
    text = resp.content if hasattr(resp, "content") else str(resp)

    logger.info(f"[conversational_response_agent] LLM response: {text}")
    return {"conversational_response": text}

def fetch_data_agent(state: ForecastState) -> ForecastState:
    logger.info(
        f"[fetch_data_agent] Fetching all available data for product {state['product_id']}"
    )

    db: Session = SessionLocal()
    try:
        q = db.query(SalesData.sales_date, SalesData.sales_quantity).filter(
            SalesData.product_id == state["product_id"]
        )

        rows = q.order_by(SalesData.sales_date).all()

    finally:
        db.close()

    if not rows:
        logger.warning("[fetch_data_agent] No rows found.")
        ts = pd.DataFrame(columns=["sales_date", "sales_quantity"])
        last_date = date.today()
    else:
        logger.info(f"[fetch_data_agent] Retrieved {len(rows)} rows.")
        ts = pd.DataFrame(rows, columns=["sales_date", "sales_quantity"])
        ts["sales_date"] = pd.to_datetime(ts["sales_date"])
        ts.set_index("sales_date", inplace=True)
        last_date = ts.index.max().date()

    logger.info(f"[fetch_data_agent] Last date in dataset: {last_date}")

    return {
        "time_series": ts,
        "last_date": last_date
    }


def extract_params_agent(state: ForecastState) -> ForecastState:
    llm = get_llm()
    user_query = state.get("user_query", "")
    today = date.today()
    last_date = state.get("last_date", today)

    parser = params_parser

    prompt = fotecasting_extract_params_prompt
    formatted = prompt.format(
        format_instructions=parser.get_format_instructions(),
        user_query=user_query,
        today=today,
        last_date=last_date
    )

    response = llm.invoke(formatted)
    parsed = parser.parse(response.content)

    history_start = (
        date.fromisoformat(parsed.history_start)
        if parsed.history_start else None
    )
    history_end = (
        date.fromisoformat(parsed.history_end)
        if parsed.history_end else None
    )

    start_horizon = parsed.start_horizon
    end_horizon = parsed.end_horizon
    single_day = parsed.single_day
    granularity = parsed.granularity

    logger.info(
        f"[extract_params_agent] Parsed params → start_horizon={start_horizon}, "
        f"end_horizon={end_horizon}, single_day={single_day}, granularity={granularity}, "
        f"history_start={history_start}, history_end={history_end}, last_date={last_date}"
    )

    return {
        "start_horizon": start_horizon,
        "end_horizon": end_horizon,
        "single_day": single_day,
        "granularity": granularity,
        "history_start": history_start,
        "history_end": history_end,
    }


def filter_data_agent(state: ForecastState) -> ForecastState:
    """
    Apply history_start and history_end filters if specified.
    """
    ts = state["time_series"]
    history_start = state.get("history_start")
    history_end = state.get("history_end")

    if ts.empty:
        logger.warning("[filter_data_agent] Empty time series, skipping filter")
        return {}

    original_len = len(ts)

    if history_start:
        ts = ts[ts.index >= pd.Timestamp(history_start)]
        logger.info(f"[filter_data_agent] Filtered by history_start={history_start}")

    if history_end:
        ts = ts[ts.index <= pd.Timestamp(history_end)]
        logger.info(f"[filter_data_agent] Filtered by history_end={history_end}")

    filtered_len = len(ts)
    logger.info(f"[filter_data_agent] Data filtered: {original_len} → {filtered_len} rows")

    # Update last_date after filtering
    if not ts.empty:
        last_date = ts.index.max().date()
        logger.info(f"[filter_data_agent] Updated last_date after filtering: {last_date}")
    else:
        last_date = state.get("last_date")

    return {
        "time_series": ts,
        "last_date": last_date
    }


def preprocess_agent(state: ForecastState) -> ForecastState:
    ts = state["time_series"]
    granularity = state.get("granularity", "daily")
    
    logger.info(f"[preprocess_agent] Starting. Rows={len(ts)}, Granularity={granularity}")

    if ts.empty:
        logger.warning("[preprocess_agent] Empty series → creating dummy")
        today = pd.Timestamp.today().normalize()
        ts = pd.DataFrame({"sales_quantity": [0]}, index=[today])

    # For daily: fill missing days
    if granularity == "daily":
        start, end = ts.index.min(), ts.index.max()
        full_idx = pd.date_range(start=start, end=end, freq="D")
        ts = ts.reindex(full_idx).fillna(0.0)
    
    # For monthly: aggregate to month level, KEEP ZEROS
    elif granularity == "monthly":
        logger.info("[preprocess_agent] Aggregating to monthly")
        ts = ts.resample("MS").sum()  # MS = Month Start
        # DON'T remove zeros - keep time series structure intact
    
    # For yearly: aggregate to year level, KEEP ZEROS
    elif granularity == "yearly":
        logger.info("[preprocess_agent] Aggregating to yearly")
        ts = ts.resample("YS").sum()  # YS = Year Start
        # DON'T remove zeros - keep time series structure intact

    logger.info(f"[preprocess_agent] Finished. Final rows={len(ts)}, "
               f"Range: {ts.index.min()} to {ts.index.max()}")

    return {"time_series": ts}

from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

def arima_agent(state: ForecastState) -> ForecastState:
    logger.info("[arima_agent] Starting multi-granularity forecasting with Prophet")

    ts = state["time_series"]
    series = ts["sales_quantity"].astype(float)
    last_date = state.get("last_date", date.today())
    granularity = state.get("granularity", "daily")
    start_horizon = int(state.get("start_horizon", 1))
    end_horizon = int(state.get("end_horizon", 1))
    
    logger.info(f"[arima_agent] Granularity: {granularity}, Last date: {last_date}")
    logger.info(f"[arima_agent] Horizons: start={start_horizon}, end={end_horizon}")

    
    if granularity == "monthly":
        freq = "MS"
        seasonal_m = 12
        prophet_freq = 'MS'  # Month Start
        
    elif granularity == "yearly":
        freq = "YS"
        seasonal_m = 1
        prophet_freq = 'YS'  # Year Start
        
    else:  # daily
        freq = "D"
        seasonal_m = 7
        prophet_freq = 'D'  # Daily
    
    forecast_length = end_horizon - start_horizon + 1
    start_offset = start_horizon - 1
    total_steps = start_offset + forecast_length
    
    logger.info(f"[arima_agent] Forecasting {forecast_length} {granularity} periods, "
               f"offset={start_offset}, total_steps={total_steps}")
    
    forecast_values = None
    
    
    try:
        logger.info("[arima_agent] Attempting Prophet forecast...")
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        df_prophet = pd.DataFrame({
            'ds': series.index,
            'y': series.values
        })
        
        # Configure Prophet based on granularity
        if granularity == "daily":
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='multiplicative',  # Better for sales with trends
                changepoint_prior_scale=0.05,  # Controls trend flexibility
                seasonality_prior_scale=10.0,  # Controls seasonality strength
                interval_width=0.95,
            )
            
        elif granularity == "monthly":
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.1,
                seasonality_prior_scale=10.0,
            )
            # Add monthly patterns
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            
        else:  # yearly
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='additive',
                changepoint_prior_scale=0.15,
                growth='linear',  # or 'logistic' if you have cap/floor
            )
        
        # Fit the model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(df_prophet)
        
        # Generate future dates
        future = model.make_future_dataframe(periods=total_steps, freq=prophet_freq)
        
        # Make predictions
        forecast_df = model.predict(future)
        
        # Extract only the future predictions we need
        all_predictions = forecast_df['yhat'].tail(total_steps).values
        
        # Extract the specific range requested
        forecast_values = [
            max(0, float(all_predictions[i]))  # Ensure non-negative
            for i in range(start_offset, total_steps)
        ]
        
        # Validate Prophet results
        forecast_mean = np.mean(forecast_values)
        forecast_std = np.std(forecast_values)
        
        logger.info(f"[arima_agent] Prophet succeeded: {len(forecast_values)} values, "
                   f"mean={forecast_mean:.2f}, std={forecast_std:.2f}")
        
        # Check if forecast is reasonable (not all zeros or constant)
        if forecast_std < 0.01 * abs(forecast_mean) and forecast_mean > 0:
            logger.warning("[arima_agent] Prophet produced near-constant forecast, will try fallback")
            forecast_values = None
        
    except Exception as e:
        logger.warning(f"[arima_agent] Prophet failed: {str(e)}")
        forecast_values = None

    if forecast_values is None:
        logger.info("[arima_agent] Falling back to ARIMA/SARIMA...")
        
        try:
            # Determine if we have enough data for seasonality
            min_data_for_seasonal = {
                "daily": 28,
                "monthly": 24,
                "yearly": 3
            }
            
            has_enough_data = len(series) >= min_data_for_seasonal.get(granularity, 10)
            seasonal = has_enough_data and granularity != "yearly"
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                model = auto_arima(
                    series,
                    seasonal=seasonal,
                    m=seasonal_m if seasonal else 1,
                    stepwise=True,
                    suppress_warnings=True,
                    error_action="ignore",
                    max_p=5,
                    max_q=5,
                    max_d=2,
                    max_P=2 if seasonal else 0,
                    max_Q=2 if seasonal else 0,
                    max_D=1 if seasonal else 0,
                    start_p=1,
                    start_q=1,
                    information_criterion='aic',
                )

                order = model.order
                seasonal_order = model.seasonal_order if seasonal else (0, 0, 0, 0)
                
                logger.info(f"[arima_agent] ARIMA order: {order}, seasonal: {seasonal_order}")
                
                # Check for poor model (random walk)
                is_random_walk = (order[0] == 0 and order[2] == 0)
                
                if is_random_walk:
                    logger.warning("[arima_agent] Random walk detected, forcing ETS fallback")
                    raise ValueError("Poor ARIMA model")
                
                # Fit SARIMA
                sarimax = SARIMAX(
                    series,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )

                fitted = sarimax.fit(disp=False, maxiter=200)
                all_preds = fitted.get_forecast(steps=total_steps).predicted_mean
                
                forecast_values = [
                    max(0, float(all_preds.iloc[i]))
                    for i in range(start_offset, total_steps)
                ]
                
                forecast_std = np.std(forecast_values)
                forecast_mean = np.mean(forecast_values)
                
                logger.info(f"[arima_agent] ARIMA succeeded: mean={forecast_mean:.2f}, std={forecast_std:.2f}")

        except Exception as e:
            logger.warning(f"[arima_agent] ARIMA failed: {str(e)}")
            forecast_values = None

    
    if forecast_values is None:
        logger.info("[arima_agent] Falling back to ETS...")
        
        try:
            use_seasonal = (
                granularity in ["daily", "monthly"] and 
                len(series) >= 2 * seasonal_m
            )
            
            # Try additive first
            try:
                ets = ExponentialSmoothing(
                    series,
                    trend="add",
                    seasonal="add" if use_seasonal else None,
                    seasonal_periods=seasonal_m if use_seasonal else None,
                    damped_trend=True,
                ).fit(optimized=True)
                
            except:
                # Fallback to multiplicative
                logger.info("[arima_agent] Trying multiplicative ETS")
                ets = ExponentialSmoothing(
                    series + 1,  # Avoid zeros
                    trend="mul",
                    seasonal="mul" if use_seasonal else None,
                    seasonal_periods=seasonal_m if use_seasonal else None,
                    damped_trend=True,
                ).fit(optimized=True)

            all_preds = ets.forecast(total_steps)
            forecast_values = [
                max(0, float(all_preds[i]))
                for i in range(start_offset, total_steps)
            ]

            logger.info(f"[arima_agent] ETS succeeded: {len(forecast_values)} values")

        except Exception as e:
            logger.error(f"[arima_agent] ETS failed: {str(e)}")
            forecast_values = None

    
    if forecast_values is None:
        logger.warning("[arima_agent] All models failed, using trend-based fallback")
        
        # Use recent trend
        window = min(90 if granularity == "daily" else 12, len(series) // 2)
        recent = series.tail(window)
        
        # Calculate trend using linear regression
        from scipy.stats import linregress
        x = np.arange(len(recent))
        slope, intercept, _, _, _ = linregress(x, recent.values)
        
        # Project forward
        last_value = float(series.iloc[-1])
        base_trend = [last_value + slope * i for i in range(1, total_steps + 1)]
        
        # Add seasonal component if available
        if len(series) >= seasonal_m * 2:
            # Extract seasonal pattern from last periods
            seasonal_pattern = []
            for i in range(seasonal_m):
                period_values = series.iloc[i::seasonal_m].tail(3)  # Last 3 cycles
                seasonal_pattern.append(period_values.mean() - series.mean())
            
            # Apply seasonal pattern
            forecast_values = []
            for i in range(start_offset, total_steps):
                trend_val = base_trend[i]
                seasonal_idx = i % len(seasonal_pattern)
                seasonal_adj = seasonal_pattern[seasonal_idx]
                forecast_values.append(max(0, trend_val + seasonal_adj))
        else:
            # Just use trend with small noise
            std = float(series.std())
            forecast_values = [
                max(0, base_trend[i] + np.random.normal(0, std * 0.05))
                for i in range(start_offset, total_steps)
            ]
        
        logger.info(f"[arima_agent] Trend-based forecast: mean={np.mean(forecast_values):.2f}")
    

    last_ts_date = ts.index.max()
    
    if granularity == "daily":
        forecast_index = pd.date_range(
            start=last_ts_date + timedelta(days=start_horizon),
            periods=len(forecast_values),
            freq="D",
        )
        forecast_dict = {
            d.date().isoformat(): round(v, 2) 
            for d, v in zip(forecast_index, forecast_values)
        }
        
    elif granularity == "monthly":
        forecast_index = pd.date_range(
            start=last_ts_date + pd.DateOffset(months=start_horizon),
            periods=len(forecast_values),
            freq="MS",
        )
        forecast_dict = {
            d.strftime("%Y-%m"): round(v, 2) 
            for d, v in zip(forecast_index, forecast_values)
        }
        
    else:  # yearly
        forecast_index = pd.date_range(
            start=last_ts_date + pd.DateOffset(years=start_horizon),
            periods=len(forecast_values),
            freq="YS",
        )
        forecast_dict = {
            str(d.year): round(v, 2) 
            for d, v in zip(forecast_index, forecast_values)
        }

    logger.info(f"[arima_agent] Forecast complete: {list(forecast_dict.keys())[:5]}... "
               f"({len(forecast_dict)} total)")

    return {"forecast": forecast_dict}


def report_agent(state: ForecastState) -> ForecastState:
    logger.info("[report_agent] Generating LLM summary")

    forecast = state["forecast"]
    granularity = state.get("granularity", "daily")
    single_day = state.get("single_day", False)
    
    llm = get_llm()

    # Granularity labels
    period_label = {
        "daily": "day",
        "monthly": "month",
        "yearly": "year"
    }.get(granularity, "period")

    # Single period forecast
    if single_day:
        target_key = list(forecast.keys())[0] if forecast else None
        value = forecast.get(target_key) if target_key else None

        if value is None:
            logger.warning(f"[report_agent] No forecast found")
            text = "No forecast available."
            return {
                "report": text,
                "forecast": {}
            }

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"Provide a concise sales forecast summary for a manufacturing analyst ({period_label}-level)."),
            ("user", f"{period_label.capitalize()}: {target_key}"),
            ("user", f"Forecasted units: {value:.2f}")
        ])

        formatted = prompt.format()
        resp = llm.invoke(formatted)
        text = resp.content if hasattr(resp, "content") else str(resp)

        logger.info(f"[report_agent] Single {period_label} summary generated")

        return {
            "report": text,
            "forecast": {target_key: round(value, 2)}
        }

    # Multi-period forecast
    values = list(forecast.values())
    total = sum(values)
    avg = total / len(values) if values else 0

    dates = list(forecast.keys())
    start_period = dates[0] if dates else "N/A"
    end_period = dates[-1] if dates else "N/A"
    num_periods = len(dates)

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Summarize this {period_label}-level demand forecast for a manufacturing analyst. Provide a clear, concise summary in 2-3 sentences."),
        ("user", f"Forecast period: {start_period} to {end_period} ({num_periods} {period_label}s)"),
        ("user", f"Total forecasted demand: {total:.2f} units"),
        ("user", f"Average {period_label}ly demand: {avg:.2f} units")
    ])

    formatted = prompt.format()
    resp = llm.invoke(formatted)
    text = resp.content if hasattr(resp, "content") else str(resp)

    logger.info(f"[report_agent] Multi-{period_label} summary generated")

    return {"report": text}



def should_continue_forecast(state: ForecastState):
    decision = "forecast" if state.get("is_forecast_request") else "conversation"
    logger.info(f"[branch] Routing → {decision}")
    return decision



builder = StateGraph(ForecastState)

builder.add_node("classify_query_agent", classify_query_agent)
builder.add_node("conversational_response_agent", conversational_response_agent)
builder.add_node("fetch_data_agent", fetch_data_agent)
builder.add_node("extract_params_agent", extract_params_agent)
builder.add_node("filter_data_agent", filter_data_agent)
builder.add_node("preprocess_agent", preprocess_agent)
builder.add_node("arima_agent", arima_agent)
builder.add_node("report_agent", report_agent)

builder.set_entry_point("classify_query_agent")

builder.add_conditional_edges(
    "classify_query_agent",
    should_continue_forecast,
    {
        "forecast": "fetch_data_agent",
        "conversation": "conversational_response_agent",
    }
)

# Forecast path
builder.add_edge("fetch_data_agent", "extract_params_agent")
builder.add_edge("extract_params_agent", "filter_data_agent")
builder.add_edge("filter_data_agent", "preprocess_agent")
builder.add_edge("preprocess_agent", "arima_agent")
builder.add_edge("arima_agent", "report_agent")
builder.add_edge("report_agent", END)

# Conversation path
builder.add_edge("conversational_response_agent", END)

demand_forecast_workflow = builder.compile()