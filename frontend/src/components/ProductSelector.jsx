import React from "react";

function ProductSelector({
  organizations,
  products,
  selectedOrgId,
  selectedProductId,
  onOrgChange,
  onProductChange,
}) {
  return (
    <div>

      <div className="field-group">
        <label htmlFor="product-select">Product</label>
        <select
          id="product-select"
          value={selectedProductId ?? ""}
          onChange={(e) => onProductChange(Number(e.target.value))}
          disabled={!selectedOrgId}
        >
          <option value="" disabled>
            {selectedOrgId ? "Select product…" : "Select organization first"}
          </option>
          {products.map((p) => (
            <option key={p.product_id} value={p.product_id}>
              {p.product_name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default ProductSelector;


