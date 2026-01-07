import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { TrendingUp, BarChart3, Calendar, Upload, ShoppingCart } from "lucide-react";

function DashboardLayout() {
  const { org, signOut } = useAuth();

  return (
    <div className="h-screen bg-white flex overflow-hidden">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
        <div className="px-6 py-5 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-1">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <span className="text-base font-semibold text-gray-900">
              Demand Studio
            </span>
          </div>
          {org && (
            <div className="text-xs text-gray-500 ml-11">
              {org.org_name}
            </div>
          )}
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-1">
          <NavLink
            to="/app/overview"
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-50"
              }`
            }
          >
            <BarChart3 className="h-4 w-4" />
            <span>Dashboard</span>
          </NavLink>
          
          <NavLink
            to="/app/forecast"
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-50"
              }`
            }
          >
            <Calendar className="h-4 w-4" />
            <span>Forecast</span>
          </NavLink>
          
          <NavLink
            to="/app/sales"
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-50"
              }`
            }
          >
            <ShoppingCart className="h-4 w-4" />
            <span>Sales Data</span>
          </NavLink>
          
          <NavLink
            to="/app/import"
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-50"
              }`
            }
          >
            <Upload className="h-4 w-4" />
            <span>Import Data</span>
          </NavLink>
        </nav>
        
        <div className="px-4 py-4 border-t border-gray-200">
          <button
            onClick={signOut}
            className="w-full text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg px-4 py-2 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;