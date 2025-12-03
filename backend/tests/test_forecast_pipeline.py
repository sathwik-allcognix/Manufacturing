import pandas as pd

from app.agents.forecast_graph import preprocess_agent, arima_agent, ForecastState


def test_forecast_pipeline_basic():
    dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
    ts = pd.DataFrame({"sales_quantity": [i for i in range(10)]}, index=dates)
    state: ForecastState = {
        "product_id": 1,
        "days": 7,
        "time_series": ts,
        "forecast": {},
        "report": "",
    }

    state = {**state, **preprocess_agent(state)}
    assert state["time_series"] is not None
    assert not state["time_series"].isna().any().any()

    state = {**state, **arima_agent(state)}
    forecast = state["forecast"]
    assert len(forecast) == 7
    # All keys should be ISO date strings
    for k in forecast.keys():
        assert isinstance(k, str)


