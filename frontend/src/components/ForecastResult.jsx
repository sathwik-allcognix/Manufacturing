import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function ForecastResult({ result }) {
  const data = useMemo(
    () =>
      result
        ? Object.entries(result.forecast).map(([date, qty]) => ({
            date,
            quantity: qty,
          }))
        : [],
    [result]
  );

  if (!result) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">Forecast</div>
          <span className="panel-badge">Idle</span>
        </div>
        <p className="report-text">
          Select a product and horizon, then run the forecast to see ARIMA-based
          projections and an LLM-generated narrative summary.
        </p>
      </div>
    );
  }

  const total = Object.values(result.forecast).reduce((acc, v) => acc + v, 0);
  const avg = total / (Object.keys(result.forecast).length || 1);

  return (
    <>
      <div className="results-header">
        <div className="results-title">Demand forecast</div>
        <div className="results-meta">
          <span className="chip">
            <span className="chip-dot" />
            {result.days}-day horizon
          </span>
          &nbsp;&nbsp;
          <span className="chip">
            Σ {total.toFixed(1)} units · μ {avg.toFixed(1)} / day
          </span>
        </div>
      </div>

      <div className="results-grid">
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">Time series</div>
            <span className="panel-badge">ARIMA</span>
          </div>
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#020617",
                    border: "1px solid #4b5563",
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#e5e7eb" }}
                />
                <Line
                  type="monotone"
                  dataKey="quantity"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">LLM summary</div>
            <span className="panel-badge">Groq + LangGraph</span>
          </div>
          <p className="report-text">{result.report}</p>
        </div>
      </div>

      <div className="panel" style={{ marginTop: "1rem" }}>
        <div className="panel-header">
          <div className="panel-title">Raw daily forecast</div>
          <span className="panel-badge">{data.length} days</span>
        </div>
        <table className="forecast-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{row.quantity.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default ForecastResult;


