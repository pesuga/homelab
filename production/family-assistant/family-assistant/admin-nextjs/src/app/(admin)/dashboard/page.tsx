"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiClient, DashboardHealth } from "@/lib/api-client";

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const [health, setHealth] = useState<DashboardHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      try {
        const healthData = await apiClient.getDashboardHealth();
        setHealth(healthData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold">Please sign in to view the dashboard</h1>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-4">Loading dashboard...</h1>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-gray-800 dark:text-white">
          Welcome, {user?.first_name}!
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          Family Assistant Admin Dashboard
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* User Info Card */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
            User Information
          </h2>
          <div className="space-y-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Email:</span> {user?.email}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Role:</span> {user?.role}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Display Name:</span> {user?.display_name}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Admin:</span>{" "}
              <span className={user?.is_admin ? "text-green-600" : "text-gray-600"}>
                {user?.is_admin ? "Yes" : "No"}
              </span>
            </p>
          </div>
        </div>

        {/* System Health Card */}
        {health && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
              System Health
            </h2>
            <div className="space-y-2">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-medium">Status:</span>{" "}
                <span className={health.status === "healthy" ? "text-green-600" : "text-red-600"}>
                  {health.status}
                </span>
              </p>
              {Object.entries(health.components).map(([key, value]) => (
                <p key={key} className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">{key}:</span>{" "}
                  <span className={value.status === "healthy" ? "text-green-600" : "text-red-600"}>
                    {value.status}
                  </span>
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions Card */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <button className="w-full px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              Manage Families
            </button>
            <button className="w-full px-4 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
              View Memories
            </button>
            <button className="w-full px-4 py-2 text-sm text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
              System Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
