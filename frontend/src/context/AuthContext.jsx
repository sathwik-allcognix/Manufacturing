import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, registerOrganization, setAuthToken } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [org, setOrg] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    const storedOrgId = localStorage.getItem("org_id");
    const storedOrgName = localStorage.getItem("org_name");
    if (storedToken && storedOrgId) {
      setAuthToken(storedToken);
      setToken(storedToken);
      setOrg({ org_id: Number(storedOrgId), org_name: storedOrgName });
    }
    setLoading(false);
  }, []);

  const signIn = async ({ org_name, password }) => {
    const res = await apiLogin({ org_name, password });
    setAuthToken(res.access_token);
    setToken(res.access_token);
    const orgData = { org_id: res.org_id, org_name: res.org_name };
    setOrg(orgData);
    localStorage.setItem("auth_token", res.access_token);
    localStorage.setItem("org_id", String(res.org_id));
    localStorage.setItem("org_name", res.org_name);
  };

  const registerAndSignIn = async ({ org_name, password }) => {
    await registerOrganization({ org_name, password });
    await signIn({ org_name, password });
  };

  const signOut = () => {
    setOrg(null);
    setToken(null);
    setAuthToken(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("org_id");
    localStorage.removeItem("org_name");
  };

  const value = {
    org,
    token,
    loading,
    isAuthenticated: !!org && !!token,
    signIn,
    registerAndSignIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}


