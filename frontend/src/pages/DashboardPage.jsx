import React, { useEffect, useState, useRef } from "react";
import ProductSelector from "../components/ProductSelector";
import { useAuth } from "../context/AuthContext";
import { createProduct, listProductsByOrg, getForecast, getNlpForecast } from "../api";
import ForecastBubble from "../components/ForecastBubble";
import { Send, TrendingUp } from "lucide-react";

function DashboardPage() {
  const { org } = useAuth();
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState();
  const [loading, setLoading] = useState(false);
  const [nlpLoading, setNlpLoading] = useState(false);
  const [nlpQuery, setNlpQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  useEffect(() => {
    const loadProducts = async () => {
      if (!org) return;
      try {
        const res = await listProductsByOrg(org.org_id);
        setProducts(res);
        if (res.length > 0) setSelectedProductId(res[0].product_id);
      } catch (err) {
        console.error(err);
      }
    };
    loadProducts();
  }, [org]);

  const handleProductChange = (productId) => {
    setSelectedProductId(productId);
  };

  const handleRunNlpForecast = async (e) => {
    e.preventDefault();
    if (!selectedProductId || !nlpQuery.trim()) return;

    const userMessage = nlpQuery.trim();
    setNlpQuery("");
    setNlpLoading(true);

    setChatHistory((prev) => [...prev, { type: "user", content: userMessage }]);

    try {
      const res = await getNlpForecast(selectedProductId, userMessage);

      if (res.is_forecast_request) {
        setChatHistory((prev) => [
          ...prev,
          { type: "forecast", data: res }
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          {
            type: "assistant",
            content: res.conversational_response || "I'm here to help!"
          }
        ]);
      }

    } catch (err) {
      console.error(err);
      setChatHistory((prev) => [
        ...prev,
        {
          type: "assistant",
          content: "Sorry, something went wrong."
        }
      ]);
    } finally {
      setNlpLoading(false);
    }
  };

  return (
    <div className="h-full bg-white flex flex-col overflow-hidden">
      {/* Top Bar */}
      <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b border-gray-200 px-6 py-4 z-10">
        {org && (
          <ProductSelector
            organizations={[org]}
            products={products}
            selectedOrgId={org.org_id}
            selectedProductId={selectedProductId}
            onOrgChange={() => {}}
            onProductChange={handleProductChange}
          />
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          {chatHistory.length === 0 && (
            <div className="text-center py-20">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 mb-4">
                <TrendingUp className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                How can I help you today?
              </h2>
              <p className="text-gray-500">
                Ask for a forecast or any insights about your products
              </p>
            </div>
          )}

          {chatHistory.map((msg, i) => {
            if (msg.type === "forecast") {
              return (
                <div key={i} className="flex justify-start">
                  <ForecastBubble data={msg.data} />
                </div>
              );
            }

            return (
              <div
                key={i}
                className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-3xl px-5 py-3 rounded-2xl text-sm ${
                    msg.type === "user"
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            );
          })}

          {nlpLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-5 py-3 rounded-2xl">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200">
        <form onSubmit={handleRunNlpForecast} className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex gap-3 items-center bg-gray-100 rounded-2xl px-4 py-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:bg-white transition-all">
            <input
              type="text"
              className="flex-1 bg-transparent border-none focus:outline-none text-sm placeholder-gray-500"
              placeholder="Ask anything about your demand forecasts..."
              value={nlpQuery}
              onChange={(e) => setNlpQuery(e.target.value)}
              disabled={nlpLoading}
            />
            <button
              type="submit"
              disabled={!nlpQuery.trim() || nlpLoading}
              className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-500 text-white disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DashboardPage;