import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

export async function registerOrganization({ org_name, password, industry_type, address }) {
  const res = await api.post("/auth/register", {
    org_name,
    password,
    industry_type,
    address,
  });
  return res.data;
}

export async function login({ org_name, password }) {
  const form = new URLSearchParams();
  form.append("username", org_name);
  form.append("password", password);
  const res = await api.post("/auth/token", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function createProduct(input) {
  const res = await api.post("/product", input);
  return res.data;
}

export async function listProductsByOrg(orgId) {
  const res = await api.get(`/product/by_org/${orgId}`);
  return res.data;
}

export async function createSalesEntry(input) {
  await api.post("/sales", input);
}

export async function getSalesByProduct(productId) {
  const res = await api.get(`/sales/by_product/${productId}`);
  return res.data;
}

export async function getSalesByOrg(orgId) {
  const res = await api.get(`/sales/by_org/${orgId}`);
  return res.data;
}

export async function getForecast(productId, days) {
  const res = await api.get(`/forecast/${productId}`, {
    params: { days },
  });
  return res.data;
}

export async function getNlpForecast(productId, query) {
  const res = await api.post("/forecast/forecast", {
    product_id: productId,
    query,
  });
  return res.data;
}


