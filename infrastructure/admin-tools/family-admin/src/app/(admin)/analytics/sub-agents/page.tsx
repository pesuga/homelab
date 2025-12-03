"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useAnalytics } from "@/hooks/useAnalytics";
import ExecutionTraceModal from "@/components/analytics/ExecutionTraceModal";
import { ApexOptions } from "apexcharts";
import dynamic from "next/dynamic";

// Dynamically import ReactApexChart
const ReactApexChart = dynamic(() => import("react-apexcharts"), {
  ssr: false,
});

export default function SubAgentAnalytics() {
  const { isAuthenticated } = useAuth();
  const {
    overview,
    traceData,
    chatOverview,
    chatLogs,
    tokenStats,
    loading,
    error,
    fetchTrace,
    refreshOverview,
    refreshChatAnalytics,
    refreshChatLogs,
    refreshTokenStats
  } = useAnalytics();
  const [activeTab, setActiveTab] = useState<"overview" | "chatlogs">("overview");
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [chatTimeRange, setChatTimeRange] = useState<string>("24h");

  // Handle execution row click
  const handleExecutionClick = async (executionId: string) => {
    setSelectedExecutionId(executionId);
    await fetchTrace(executionId);
  };

  // Close modal
  const handleCloseModal = () => {
    setSelectedExecutionId(null);
  };

  if (!isAuthenticated) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold">Please sign in to view analytics</h1>
      </div>
    );
  }

  if (loading && !overview) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  // Chart configuration for agent popularity
  const chartOptions: ApexOptions = {
    colors: ["#465fff"],
    chart: {
      fontFamily: "Outfit, sans-serif",
      type: "bar",
      height: 300,
      toolbar: {
        show: false,
      },
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: "55%",
        borderRadius: 5,
        borderRadiusApplication: "end",
      },
    },
    dataLabels: {
      enabled: false,
    },
    stroke: {
      show: true,
      width: 4,
      colors: ["transparent"],
    },
    xaxis: {
      categories: overview?.agent_popularity.map((a) => a.agent) || [],
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
    },
    legend: {
      show: false,
    },
    yaxis: {
      title: {
        text: "Executions",
      },
    },
    grid: {
      yaxis: {
        lines: {
          show: true,
        },
      },
    },
    fill: {
      opacity: 1,
    },
    tooltip: {
      y: {
        formatter: (val: number) => `${val} executions`,
      },
    },
  };

  const chartSeries = [
    {
      name: "Executions",
      data: overview?.agent_popularity.map((a) => a.count) || [],
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-800 dark:text-white">
            Sub-Agent Analytics
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Monitor sub-agent performance and execution patterns
          </p>
        </div>
        <button
          onClick={refreshOverview}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "overview"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            Sub-Agent Analytics
          </button>
          <button
            onClick={() => {
              setActiveTab("chatlogs");
              refreshChatAnalytics(chatTimeRange);
              refreshChatLogs(50, chatTimeRange);
              refreshTokenStats("7d");
            }}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "chatlogs"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            Chat Logs
          </button>
        </nav>
      </div>

      {/* Overview Tab Content */}
      {activeTab === "overview" && overview && (
        <div className="space-y-6">
          {/* Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Executions (24h)"
              value={overview.metrics.total_executions_24h.toLocaleString()}
              icon="📊"
            />
            <MetricCard
              title="Success Rate"
              value={`${(overview.metrics.success_rate * 100).toFixed(1)}%`}
              icon="✅"
            />
            <MetricCard
              title="Avg Response Time"
              value={`${overview.metrics.avg_response_time_ms.toFixed(0)}ms`}
              icon="⚡"
            />
            <MetricCard
              title="Total Tokens"
              value={overview.metrics.total_tokens.toLocaleString()}
              icon="🎯"
            />
          </div>

          {/* Agent Popularity Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
              Agent Popularity
            </h2>
            <div className="overflow-x-auto">
              <div className="min-w-[600px]">
                <ReactApexChart
                  options={chartOptions}
                  series={chartSeries}
                  type="bar"
                  height={300}
                />
              </div>
            </div>
          </div>

          {/* Recent Executions Table */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                Recent Executions
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Agent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Tokens
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {overview.recent_executions.map((execution) => (
                    <tr
                      key={execution.execution_id}
                      onClick={() => handleExecutionClick(execution.execution_id)}
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {new Date(execution.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-800 dark:text-white">
                        {execution.agent}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            execution.success
                              ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                              : "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
                          }`}
                        >
                          {execution.success ? "Success" : "Failed"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {execution.response_time_ms.toFixed(0)}ms
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {execution.total_tokens.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Chat Logs Tab Content */}
      {activeTab === "chatlogs" && (
        <div className="space-y-6">
          {/* Chat Overview Metrics */}
          {chatOverview && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title="Total Requests"
                value={chatOverview.total_requests.toLocaleString()}
                icon="💬"
              />
              <MetricCard
                title="Total Tokens"
                value={chatOverview.total_tokens.toLocaleString()}
                icon="🎯"
              />
              <MetricCard
                title="Estimated Cost"
                value={`$${chatOverview.estimated_cost_usd.toFixed(4)}`}
                icon="💰"
              />
              <MetricCard
                title="Avg Latency"
                value={`${chatOverview.avg_latency_ms.toFixed(0)}ms`}
                icon="⚡"
              />
            </div>
          )}

          {/* Token Usage by Model */}
          {tokenStats && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
                Token Usage by Model (7d)
              </h2>
              <div className="space-y-3">
                {Object.entries(tokenStats.by_model).map(([model, tokens]) => (
                  <div key={model} className="flex items-center justify-between">
                    <span className="text-gray-700 dark:text-gray-300 font-medium">
                      {model}
                    </span>
                    <div className="flex items-center gap-4">
                      <div className="w-48 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${(tokens / tokenStats.total) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-gray-600 dark:text-gray-400 w-24 text-right">
                        {tokens.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chat Logs Table */}
          {chatLogs && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                  Recent Chat Sessions ({chatTimeRange})
                </h2>
                <select
                  value={chatTimeRange}
                  onChange={(e) => {
                    const newRange = e.target.value;
                    setChatTimeRange(newRange);
                    refreshChatAnalytics(newRange);
                    refreshChatLogs(50, newRange);
                  }}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white rounded border border-gray-300 dark:border-gray-600"
                >
                  <option value="24h">Last 24 hours</option>
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                </select>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Tokens
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Latency
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Cost
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {chatLogs.map((log, index) => (
                      <tr
                        key={`${log.session_id}-${index}`}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {log.user_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-800 dark:text-white">
                          {log.model_used.split("/").pop()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {log.tokens.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {log.latency_ms.toFixed(0)}ms
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          ${log.cost_usd.toFixed(6)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded ${
                              !log.error
                                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                                : "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
                            }`}
                          >
                            {!log.error ? "Success" : "Error"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Execution Trace Modal */}
      {selectedExecutionId && (
        <ExecutionTraceModal trace={traceData} onClose={handleCloseModal} />
      )}
    </div>
  );
}

// Metric Card Component
function MetricCard({ title, value, icon }: { title: string; value: string; icon: string }) {
  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );
}
