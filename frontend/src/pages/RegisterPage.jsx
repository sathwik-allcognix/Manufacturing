import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function RegisterPage() {
  const { registerAndSignIn } = useAuth();
  const navigate = useNavigate();
  const [orgName, setOrgName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerAndSignIn({ org_name: orgName, password });
      navigate("/app/overview");
    } catch (err) {
      console.error(err);
      setError("Registration failed. Try a different organization name.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 flex items-center justify-center">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-md border border-neutral-200 px-8 py-10">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-6 w-6 rounded-full bg-blue-500" />
            <span className="text-xs uppercase tracking-[0.25em] text-neutral-500">
              Demand Studio
            </span>
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900">
            Create organization
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Set up an account to start forecasting for your products.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="org-name"
              className="block text-xs font-medium text-neutral-700 mb-1"
            >
              Organization name
            </label>
            <input
              id="org-name"
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="e.g. Demo Manufacturing Co."
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="block text-xs font-medium text-neutral-700 mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          {error && (
            <div className="text-xs text-red-500">
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={!orgName || !password || loading}
            className="w-full rounded-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white text-sm font-medium py-2.5 mt-1 transition-colors"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className="mt-6 text-xs text-neutral-500 flex justify-between">
          <span>Already have an account?</span>
          <Link
            to="/login"
            className="text-blue-600 hover:underline font-medium"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;


