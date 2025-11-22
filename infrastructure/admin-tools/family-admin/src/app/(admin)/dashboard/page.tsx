"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import { useDashboardData } from "@/hooks/useDashboardData";

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const { health, stats, loading, error, refreshAll } = useDashboardData();

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
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-800 dark:text-white">
            Welcome, {user?.first_name}!
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Family Assistant Admin Dashboard
          </p>
        </div>
        <button
          onClick={refreshAll}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {error}
        </div>
      )}

      {/* System Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Memories</p>
                <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                  {stats.total_memories.toLocaleString()}
                </p>
              </div>
              <div className="text-4xl">💾</div>
            </div>
          </div>

          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Active Users</p>
                <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                  {stats.total_users}
                </p>
              </div>
              <div className="text-4xl">👥</div>
            </div>
          </div>

          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Active Conversations</p>
                <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                  {stats.active_conversations}
                </p>
              </div>
              <div className="text-4xl">💬</div>
            </div>
          </div>

          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Cache Hit Rate</p>
                <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                  {(stats.cache_hit_rate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Phase 2 Memory System Health */}
        {health && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                Memory System Health
              </h2>
              <span
                className={`px-3 py-1 rounded text-sm font-medium ${
                  health.status === "healthy"
                    ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                    : health.status === "degraded"
                    ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
                    : "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
                }`}
              >
                {health.status}
              </span>
            </div>

            <div className="space-y-3">
              {/* Redis */}
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔴</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">Redis Cache</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Latency: {health.redis.latency_ms.toFixed(2)}ms
                    </p>
                  </div>
                </div>
                <span
                  className={`w-3 h-3 rounded-full ${
                    health.redis.connected ? "bg-green-500" : "bg-red-500"
                  }`}
                ></span>
              </div>

              {/* Mem0 */}
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🧠</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">Mem0 AI Memory</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Status: {health.mem0.status}
                    </p>
                  </div>
                </div>
                <span
                  className={`w-3 h-3 rounded-full ${
                    health.mem0.connected ? "bg-green-500" : "bg-red-500"
                  }`}
                ></span>
              </div>

              {/* Qdrant */}
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🗄️</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">Qdrant Vector DB</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Collections: {health.qdrant.collections}
                    </p>
                  </div>
                </div>
                <span
                  className={`w-3 h-3 rounded-full ${
                    health.qdrant.connected ? "bg-green-500" : "bg-red-500"
                  }`}
                ></span>
              </div>

              {/* Ollama */}
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🤖</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">Ollama LLM</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Models: {health.ollama.models.join(", ") || "None"}
                    </p>
                  </div>
                </div>
                <span
                  className={`w-3 h-3 rounded-full ${
                    health.ollama.connected ? "bg-green-500" : "bg-red-500"
                  }`}
                ></span>
              </div>
            </div>
          </div>
        )}

        {/* Memory Breakdown by Layer */}
        {stats && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
              Memory Distribution by Layer
            </h2>
            <div className="space-y-3">
              {Object.entries(stats.memories_by_layer).map(([layer, count]) => {
                const total = stats.total_memories || 1;
                const percentage = ((count / total) * 100).toFixed(1);
                return (
                  <div key={layer}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {layer}
                      </span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {count.toLocaleString()} ({percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                <span className="font-medium">Storage Usage:</span>{" "}
                {(stats.storage_usage_mb / 1024).toFixed(2)} GB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* User Info & Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
