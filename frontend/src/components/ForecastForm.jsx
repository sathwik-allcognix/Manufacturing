import React, { useState } from "react";

function ForecastForm({ productId, onRunForecast, loading }) {
  const [days, setDays] = useState(30);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!productId) {
      setError("Select a product first.");
      return;
    }
    if (days < 1 || days > 365) {
      setError("Days must be between 1 and 365.");
      return;
    }
    await onRunForecast(days);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="section-title">Forecast Settings</div>
      <div className="field-group">
        <label htmlFor="days-input">Horizon (days)</label>
        <input
          id="days-input"
          type="number"
          min={1}
          max={365}
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
        />
      </div>
      {error && <div className="error-text">{error}</div>}
      <button className="primary" type="submit" disabled={!productId || loading}>
        {loading ? "Running forecast…" : "Run Forecast"}
      </button>
      <div className="pill-row">
        <div className="pill">
          <strong>Tip:</strong>&nbsp;Use 30 / 60 / 90 days for production planning.
        </div>
      </div>
    </form>
  );
}

export default ForecastForm;


