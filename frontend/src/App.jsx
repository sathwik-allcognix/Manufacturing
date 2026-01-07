import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import OverviewPage from "./pages/OverviewPage";
import DataImportPage from "./pages/DataImportPage"; // Add this import
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layout/DashboardLayout";
import SalesDataPage from "./pages/SalesDataPage";
function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="forecast" element={<DashboardPage />} />
          <Route path="import" element={<DataImportPage />} /> 
          <Route path="/app/sales" element={<SalesDataPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/app/overview" replace />} />
    </Routes>
  );
}

export default App;