"use client";

import React, { useEffect, useState } from "react";
import type { Metadata } from "next";
import { useAuth } from "@/context/AuthContext";
import { apiClient, DashboardHealth } from "@/lib/api-client";
import AdaptiveHomeScreen from "@/components/family/AdaptiveHomeScreen";

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
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error}
        </div>
      )}

      <AdaptiveHomeScreen />

      {/* Admin-Only Section */}
      {user?.is_admin && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                <span className="text-green-600">
                  Yes
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
                {health.components && Object.entries(health.components).map(([key, value]) => (
                  <p key={key} className="text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-medium capitalize">{key}:</span>{" "}
                    <span className="text-green-600">
                      Connected
                    </span>
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Admin Quick Actions Card */}
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
              Admin Actions
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
      )}
    </div>
  );
}
