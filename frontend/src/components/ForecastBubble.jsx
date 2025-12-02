import React, { useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";
import { Download } from "lucide-react";

function ForecastBubble({ data }) {
  const chartData = useMemo(
    () =>
      Object.entries(data.forecast).map(([date, qty]) => ({
        date,
        quantity: qty
      })),
    [data]
  );

  const total = Object.values(data.forecast).reduce((a, v) => a + v, 0);
  const avg = total / chartData.length;
  
  // Get granularity from data, default to 'daily'
  const granularity = data.granularity || 'daily';
  const periods = data.periods || chartData.length;
  
  // Period labels
  const periodLabels = {
    daily: { singular: 'Day', plural: 'Days', short: 'day' },
    monthly: { singular: 'Month', plural: 'Months', short: 'month' },
    yearly: { singular: 'Year', plural: 'Years', short: 'year' }
  };
  
  const label = periodLabels[granularity] || periodLabels.daily;
  const periodText = periods === 1 ? label.singular : label.plural;

  const exportToCSV = () => {
    const csvContent = [
      ['Date', 'Quantity'],
      ...chartData.map(row => [row.date, row.quantity.toFixed(1)])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `forecast_${periods}_${granularity}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-4xl bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          {periods}-{periodText} Demand Forecast
        </h3>
        <div className="flex gap-2 items-center">
          <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full">
            ARIMA Model
          </span>
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 hover:bg-green-100 text-xs font-medium rounded-full transition-colors"
          >
            <Download className="h-3 w-3" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="w-full h-64 bg-gray-50 rounded-xl p-4">
        {chartData.length === 1 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-5xl font-bold text-blue-600 mb-2">
                {chartData[0].quantity.toFixed(1)}
              </div>
              <div className="text-sm text-gray-600 mb-1">units</div>
              <div className="text-xs text-gray-500">{chartData[0].date}</div>
            </div>
          </div>
        ) : (
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#6b7280" }}
                tickLine={{ stroke: "#e5e7eb" }}
                minTickGap={10}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7280" }}
                tickLine={{ stroke: "#e5e7eb" }}
                domain={['auto', 'auto']}
                padding={{ top: 20, bottom: 20 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="quantity"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={chartData.length <= 7}
                dotSize={6}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Total Units</div>
          <div className="text-2xl font-semibold text-gray-900">
            {total.toFixed(1)}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">
            Avg per {label.singular}
          </div>
          <div className="text-2xl font-semibold text-gray-900">
            {avg.toFixed(1)}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
        <div className="text-xs font-medium text-blue-700 mb-2">
          AI Analysis
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">{data.report}</p>
      </div>

      {/* Data Table */}
      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 list-none flex items-center gap-2">
          <span className="group-open:rotate-90 transition-transform">▶</span>
          View detailed forecast data ({chartData.length} {chartData.length === 1 ? label.short : label.short + 's'})
        </summary>
        <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-2 px-4 font-medium text-gray-700">
                  {granularity === 'yearly' ? 'Year' : 'Date'}
                </th>
                <th className="text-left py-2 px-4 font-medium text-gray-700">Quantity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {chartData.map((row) => (
                <tr key={row.date} className="hover:bg-gray-50">
                  <td className="py-2 px-4 text-gray-600">{row.date}</td>
                  <td className="py-2 px-4 text-gray-900 font-medium">
                    {row.quantity.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export default ForecastBubble;