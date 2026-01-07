import React, { useState, useEffect } from "react";
import { Plus, Edit2, Trash2, X, Search, Package, TrendingUp } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import {
  listProductsByOrg,
  getSalesByOrg,
  createSalesEntry,
  updateSalesEntry,
  deleteSalesEntry,
} from "../api";

function SalesDataPage() {
  const { org } = useAuth();
  const [products, setProducts] = useState([]);
  const [salesData, setSalesData] = useState([]);
  const [filteredSales, setFilteredSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("date-desc");
  const [showModal, setShowModal] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [formData, setFormData] = useState({
    product_id: "",
    sales_date: "",
    sales_quantity: "",
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    if (org?.org_id) {
      loadData();
    }
  }, [org]);

  useEffect(() => {
    filterSales();
  }, [selectedProduct, searchQuery, sortBy, salesData]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [productsData, salesResponse] = await Promise.all([
        listProductsByOrg(org.org_id),
        getSalesByOrg(org.org_id),
      ]);
      setProducts(productsData);
      setSalesData(salesResponse);
    } catch (error) {
      console.error("Error loading data:", error);
      setError("Failed to load data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const filterSales = () => {
    let filtered = [...salesData];

    if (selectedProduct !== "all") {
      filtered = filtered.filter(
        (sale) => sale.product_id === parseInt(selectedProduct)
      );
    }

    if (searchQuery) {
      filtered = filtered.filter((sale) => {
        const product = products.find((p) => p.product_id === sale.product_id);
        return (
          product?.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          product?.sku?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          sale.sales_date.includes(searchQuery)
        );
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "date-asc":
          return new Date(a.sales_date) - new Date(b.sales_date);
        case "date-desc":
          return new Date(b.sales_date) - new Date(a.sales_date);
        case "quantity-asc":
          return parseFloat(a.sales_quantity) - parseFloat(b.sales_quantity);
        case "quantity-desc":
          return parseFloat(b.sales_quantity) - parseFloat(a.sales_quantity);
        default:
          return 0;
      }
    });

    setFilteredSales(filtered);
  };

  const getProductName = (productId) => {
    const product = products.find((p) => p.product_id === productId);
    return product ? product.product_name : "Unknown";
  };

  const handleOpenModal = (entry = null) => {
    if (entry) {
      setEditingEntry(entry);
      setFormData({
        product_id: entry.product_id,
        sales_date: entry.sales_date,
        sales_quantity: entry.sales_quantity,
      });
    } else {
      setEditingEntry(null);
      setFormData({
        product_id: products[0]?.product_id || "",
        sales_date: new Date().toISOString().split("T")[0],
        sales_quantity: "",
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingEntry(null);
    setFormData({ product_id: "", sales_date: "", sales_quantity: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      if (editingEntry) {
        await updateSalesEntry(editingEntry.order_id, {
          sales_date: formData.sales_date,
          sales_quantity: parseFloat(formData.sales_quantity),
        });
      } else {
        await createSalesEntry({
          product_id: parseInt(formData.product_id),
          sales_date: formData.sales_date,
          sales_quantity: parseFloat(formData.sales_quantity),
        });
      }
      await loadData();
      handleCloseModal();
    } catch (error) {
      console.error("Error saving sales entry:", error);
      setError(error.response?.data?.detail || "Error saving sales entry");
    }
  };

  const handleDelete = async (orderId) => {
    if (!confirm("Are you sure you want to delete this sales entry?")) return;
    
    setError(null);
    try {
      await deleteSalesEntry(orderId);
      await loadData();
    } catch (error) {
      console.error("Error deleting sales entry:", error);
      setError("Error deleting sales entry");
    }
  };

  const calculateStats = () => {
    const total = filteredSales.reduce(
      (sum, sale) => sum + parseFloat(sale.sales_quantity),
      0
    );
    const avg = filteredSales.length > 0 ? total / filteredSales.length : 0;
    return { total: total.toFixed(2), avg: avg.toFixed(2), count: filteredSales.length };
  };

  const stats = calculateStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading sales data...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Sales Data</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage and track your sales records
            </p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            disabled={products.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4" />
            Add Sales Entry
          </button>
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-medium text-blue-900">Total Sales</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">{stats.total}</div>
            <div className="text-xs text-blue-700 mt-1">{stats.count} entries</div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="flex items-center gap-2 mb-1">
              <Package className="h-4 w-4 text-green-600" />
              <span className="text-xs font-medium text-green-900">Average</span>
            </div>
            <div className="text-2xl font-bold text-green-900">{stats.avg}</div>
            <div className="text-xs text-green-700 mt-1">per entry</div>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center gap-2 mb-1">
              <Package className="h-4 w-4 text-purple-600" />
              <span className="text-xs font-medium text-purple-900">Products</span>
            </div>
            <div className="text-2xl font-bold text-purple-900">{products.length}</div>
            <div className="text-xs text-purple-700 mt-1">with sales data</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by product name, SKU, or date..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
          <select
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          >
            <option value="all">All Products</option>
            {products.map((product) => (
              <option key={product.product_id} value={product.product_id}>
                {product.product_name}
              </option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          >
            <option value="date-desc">Date (Newest First)</option>
            <option value="date-asc">Date (Oldest First)</option>
            <option value="quantity-desc">Quantity (High to Low)</option>
            <option value="quantity-asc">Quantity (Low to High)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {products.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Products Yet</h3>
            <p className="text-gray-500">Create products first before adding sales data.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredSales.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-6 py-12 text-center text-gray-500">
                      {salesData.length === 0 
                        ? "No sales data yet. Click 'Add Sales Entry' to get started."
                        : "No sales data found matching your filters."}
                    </td>
                  </tr>
                ) : (
                  filteredSales.map((sale) => (
                    <tr key={sale.order_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {getProductName(sale.product_id)}
                        </div>
                        <div className="text-xs text-gray-500">
                          Product ID: {sale.product_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(sale.sales_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {sale.sales_quantity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleOpenModal(sale)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(sale.order_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingEntry ? "Edit Sales Entry" : "Add Sales Entry"}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product
                </label>
                <select
                  value={formData.product_id}
                  onChange={(e) =>
                    setFormData({ ...formData, product_id: e.target.value })
                  }
                  disabled={!!editingEntry}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  required
                >
                  <option value="">Select a product</option>
                  {products.map((product) => (
                    <option key={product.product_id} value={product.product_id}>
                      {product.product_name} ({product.sku || "No SKU"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sales Date
                </label>
                <input
                  type="date"
                  value={formData.sales_date}
                  onChange={(e) =>
                    setFormData({ ...formData, sales_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sales Quantity
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.sales_quantity}
                  onChange={(e) =>
                    setFormData({ ...formData, sales_quantity: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter quantity"
                  required
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingEntry ? "Update" : "Create"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SalesDataPage;