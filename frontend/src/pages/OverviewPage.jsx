import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useAuth } from "../context/AuthContext";
import ProductSelector from "../components/ProductSelector";
import { getSalesByOrg, getSalesByProduct, listProductsByOrg } from "../api";

function OverviewPage() {
  const { org } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState();
  const [orgSales, setOrgSales] = useState([]);
  const [productSales, setProductSales] = useState([]);
  const [seriesMode, setSeriesMode] = useState("product"); // 'product' | 'overall'

  useEffect(() => {
    const load = async () => {
      if (!org) return;
      try {
        const [prods, orgSalesData] = await Promise.all([
          listProductsByOrg(org.org_id),
          getSalesByOrg(org.org_id),
        ]);
        setProducts(prods);
        setOrgSales(orgSalesData);
        if (prods.length > 0) {
          const pid = prods[0].product_id;
          setSelectedProductId(pid);
          const ps = await getSalesByProduct(pid);
          setProductSales(ps);
        }
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, [org]);

  useEffect(() => {
    const loadProductSales = async () => {
      if (!selectedProductId) return;
      try {
        const ps = await getSalesByProduct(selectedProductId);
        setProductSales(ps);
      } catch (err) {
        console.error(err);
      }
    };
    loadProductSales();
  }, [selectedProductId]);

  const handleOrgChange = () => {
    // single-org dashboard; no-op
  };

  const productSeries = useMemo(
    () =>
      productSales.map((s) => ({
        date: s.sales_date,
        quantity: Number(s.sales_quantity),
      })),
    [productSales]
  );

  const overallSeries = useMemo(() => {
    const map = new Map();
    orgSales.forEach((s) => {
      const key = s.sales_date;
      const prev = map.get(key) ?? 0;
      map.set(key, prev + Number(s.sales_quantity));
    });
    return Array.from(map.entries())
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([date, quantity]) => ({ date, quantity }));
  }, [orgSales]);

  const activeSeries = seriesMode === "product" ? productSeries : overallSeries;

  return (
    <div className="min-h-screen bg-neutral-100">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-baseline justify-between mb-6">
          <div>
            <h1 className="text-xl font-semibold text-neutral-900">
              Dashboard
            </h1>
            <p className="text-sm text-neutral-500">
              Monitor historical sales and jump into forecasting when ready.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/app/forecast")}
            className="rounded-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium px-4 py-2"
          >
            Predict forecast
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6 lg:p-8">
          <div className="grid lg:grid-cols-[320px,1fr] gap-8">
            <div className="border-b lg:border-b-0 lg:border-r border-neutral-200 pb-6 lg:pb-0 lg:pr-6">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500 mb-2">
                Scope
              </div>
              {org && (
                <ProductSelector
                  organizations={[org]}
                  products={products}
                  selectedOrgId={org.org_id}
                  selectedProductId={selectedProductId}
                  onOrgChange={handleOrgChange}
                  onProductChange={setSelectedProductId}
                />
              )}
              <div className="mt-4">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500 mb-2">
                  Series
                </div>
                <div className="inline-flex rounded-full bg-neutral-100 p-1 text-xs">
                  <button
                    type="button"
                    onClick={() => setSeriesMode("product")}
                    className={`px-3 py-1 rounded-full ${
                      seriesMode === "product"
                        ? "bg-white shadow-sm text-neutral-900"
                        : "text-neutral-500"
                    }`}
                  >
                    Selected product
                  </button>
                  <button
                    type="button"
                    onClick={() => setSeriesMode("overall")}
                    className={`px-3 py-1 rounded-full ${
                      seriesMode === "overall"
                        ? "bg-white shadow-sm text-neutral-900"
                        : "text-neutral-500"
                    }`}
                  >
                    All products
                  </button>
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">
                  Sales history
                </div>
                <div className="text-xs text-neutral-500">
                  {seriesMode === "product"
                    ? "Daily units for selected product"
                    : "Aggregate daily units across products"}
                </div>
              </div>
              <div className="h-72">
                <ResponsiveContainer>
                  <LineChart data={activeSeries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 10 }}
                      stroke="#9ca3af"
                    />
                    <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "white",
                        border: "1px solid #e5e7eb",
                        fontSize: 12,
                      }}
                      labelStyle={{ color: "#111827" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="quantity"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OverviewPage;


