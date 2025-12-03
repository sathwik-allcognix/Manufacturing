import React, { useState, useEffect } from 'react';
import { Upload, FileSpreadsheet, Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

function DataImportPage() {
  const { org } = useAuth();
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [file, setFile] = useState(null);
  const [importSource, setImportSource] = useState('excel'); // 'excel' or 'salesforce'
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [salesforceConfig, setSalesforceConfig] = useState({
    username: '',
    password: '',
    security_token: '',
    domain: 'login'
  });

  useEffect(() => {
    if (org?.org_id) {
      fetchProducts();
    }
  }, [org]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/products/by_org/${org.org_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load products' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      if (validTypes.includes(selectedFile.type) || selectedFile.name.endsWith('.csv') || selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls')) {
        setFile(selectedFile);
        setMessage({ type: '', text: '' });
      } else {
        setMessage({ type: 'error', text: 'Please upload a valid CSV or Excel file' });
        setFile(null);
      }
    }
  };

  const handleExcelUpload = async () => {
    if (!selectedProduct || !file) {
      setMessage({ type: 'error', text: 'Please select a product and upload a file' });
      return;
    }

    setUploading(true);
    setMessage({ type: '', text: '' });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('product_id', selectedProduct);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/sales/import/excel', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setMessage({ 
        type: 'success', 
        text: `Successfully imported ${data.imported_count} records. ${data.skipped_count > 0 ? `Skipped ${data.skipped_count} duplicates.` : ''}` 
      });
      setFile(null);
      setSelectedProduct('');
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Failed to import data' });
    } finally {
      setUploading(false);
    }
  };

  const handleSalesforceImport = async () => {
    if (!selectedProduct) {
      setMessage({ type: 'error', text: 'Please select a product' });
      return;
    }

    if (!salesforceConfig.username || !salesforceConfig.password || !salesforceConfig.security_token) {
      setMessage({ type: 'error', text: 'Please fill in all Salesforce credentials' });
      return;
    }

    setUploading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/sales/import/salesforce', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: parseInt(selectedProduct),
          ...salesforceConfig
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Salesforce import failed');
      }

      setMessage({ 
        type: 'success', 
        text: `Successfully imported ${data.imported_count} records from Salesforce. ${data.skipped_count > 0 ? `Skipped ${data.skipped_count} duplicates.` : ''}` 
      });
      setSelectedProduct('');
      setSalesforceConfig({ username: '', password: '', security_token: '', domain: 'login' });
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Failed to import from Salesforce' });
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const csvContent = "sales_date,sales_quantity\n2024-01-01,100\n2024-01-02,150\n2024-01-03,120";
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sales_data_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Import Sales Data</h1>
          <p className="text-gray-600">Upload sales data from Excel/CSV or import from Salesforce CRM</p>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
            )}
            <p className="text-sm">{message.text}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Product <span className="text-red-500">*</span>
            </label>
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading products...</span>
              </div>
            ) : (
              <select
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={uploading}
              >
                <option value="">Choose a product</option>
                {products.map((product) => (
                  <option key={product.product_id} value={product.product_id}>
                    {product.product_name} {product.sku ? `(${product.sku})` : ''}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Import Source
            </label>
            <div className="flex gap-4">
              <button
                onClick={() => setImportSource('excel')}
                className={`flex-1 p-4 border-2 rounded-lg transition-all ${
                  importSource === 'excel'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                disabled={uploading}
              >
                <FileSpreadsheet className="h-6 w-6 mx-auto mb-2 text-green-600" />
                <p className="font-medium text-gray-900">Excel/CSV</p>
              </button>
              <button
                onClick={() => setImportSource('salesforce')}
                className={`flex-1 p-4 border-2 rounded-lg transition-all ${
                  importSource === 'salesforce'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                disabled={uploading}
              >
                <div className="h-6 w-6 mx-auto mb-2 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">SF</div>
                <p className="font-medium text-gray-900">Salesforce</p>
              </button>
            </div>
          </div>

          {importSource === 'excel' ? (
            <div>
              <div className="mb-4">
                <button
                  onClick={downloadTemplate}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download CSV Template
                </button>
                <p className="text-xs text-gray-500 mt-1">Required columns: sales_date (YYYY-MM-DD), sales_quantity</p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload File <span className="text-red-500">*</span>
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-gray-400 transition-colors">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label className="relative cursor-pointer rounded-md font-medium text-blue-600 hover:text-blue-500">
                        <span>Upload a file</span>
                        <input
                          type="file"
                          className="sr-only"
                          accept=".csv,.xlsx,.xls"
                          onChange={handleFileChange}
                          disabled={uploading}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">CSV, XLS, XLSX up to 10MB</p>
                    {file && (
                      <p className="text-sm text-green-600 font-medium mt-2">
                        Selected: {file.name}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={handleExcelUpload}
                disabled={!selectedProduct || !file || uploading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 font-medium"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="h-5 w-5" />
                    Import Data
                  </>
                )}
              </button>
            </div>
          ) : (
            <div>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Salesforce Username <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={salesforceConfig.username}
                    onChange={(e) => setSalesforceConfig({...salesforceConfig, username: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="user@example.com"
                    disabled={uploading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={salesforceConfig.password}
                    onChange={(e) => setSalesforceConfig({...salesforceConfig, password: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={uploading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Security Token <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={salesforceConfig.security_token}
                    onChange={(e) => setSalesforceConfig({...salesforceConfig, security_token: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={uploading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domain
                  </label>
                  <select
                    value={salesforceConfig.domain}
                    onChange={(e) => setSalesforceConfig({...salesforceConfig, domain: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={uploading}
                  >
                    <option value="login">Production (login.salesforce.com)</option>
                    <option value="test">Sandbox (test.salesforce.com)</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleSalesforceImport}
                disabled={!selectedProduct || uploading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 font-medium"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Importing from Salesforce...
                  </>
                ) : (
                  'Import from Salesforce'
                )}
              </button>
            </div>
          )}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">Data Format Requirements</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Sales date must be in YYYY-MM-DD format (e.g., 2024-01-15)</li>
            <li>• Sales quantity must be a positive number</li>
            <li>• Duplicate entries (same product + date) will be skipped</li>
            <li>• For Salesforce: Ensure OpportunityLineItem access is enabled</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DataImportPage;