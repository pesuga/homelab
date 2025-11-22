"use client";

import React, { useState } from "react";
import { useMCPTools, MCPTool } from "@/hooks/useMCPTools";

export default function MCPToolConnections() {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  const {
    tools,
    loading,
    error,
    connectTool,
    disconnectTool,
    testConnection,
    stats,
  } = useMCPTools();

  const statusColors = {
    connected: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
    disconnected: "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400",
    error: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
    configuring: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400",
  };

  const handleConnect = async (toolId: string) => {
    try {
      await connectTool(toolId);
      alert(`${toolId} connected successfully!`);
    } catch (error) {
      console.error("Failed to connect tool:", error);
      alert("Failed to connect tool. Please try again.");
    }
  };

  const handleDisconnect = async (toolId: string) => {
    if (confirm("Are you sure you want to disconnect this tool?")) {
      try {
        await disconnectTool(toolId);
      } catch (error) {
        console.error("Failed to disconnect tool:", error);
      }
    }
  };

  const handleTestConnection = async (toolId: string) => {
    const result = await testConnection(toolId);
    alert(result ? "Connection test successful!" : "Connection test failed.");
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return "Never";
    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
    return date.toLocaleDateString();
  };

  // Group tools by type
  const toolsByType = {
    arcade: tools.filter((t) => t.type === "arcade"),
    n8n: tools.filter((t) => t.type === "n8n"),
    mcp: tools.filter((t) => t.type === "mcp"),
    integration: tools.filter((t) => t.type === "integration"),
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-gray-800 dark:text-white">
          MCP & Tool Connections
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          Manage Model Context Protocol servers and external integrations
        </p>
      </div>

      {/* Backend Status Warning */}
      <div className="mb-6 p-4 bg-yellow-100 dark:bg-yellow-900/20 border border-yellow-400 dark:border-yellow-800 text-yellow-800 dark:text-yellow-400 rounded">
        ⚠️ MCP tool management is using mock data. Backend endpoints not yet implemented.
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Tools</p>
              <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                {stats.total}
              </p>
            </div>
            <div className="text-4xl">🔧</div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Connected</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">
                {stats.connected}
              </p>
            </div>
            <div className="text-4xl">✓</div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">MCP Servers</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                {stats.mcp}
              </p>
            </div>
            <div className="text-4xl">🧩</div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Integrations</p>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                {stats.n8n + stats.arcade}
              </p>
            </div>
            <div className="text-4xl">⚡</div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading MCP tools...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Arcade.dev Section */}
          {toolsByType.arcade.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <span>🎮</span> Arcade.dev Integration
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {toolsByType.arcade.map((tool) => (
                  <ToolCard
                    key={tool.id}
                    tool={tool}
                    selected={selectedTool === tool.id}
                    onSelect={setSelectedTool}
                    onConnect={handleConnect}
                    onDisconnect={handleDisconnect}
                    onTest={handleTestConnection}
                    statusColors={statusColors}
                    formatLastSync={formatLastSync}
                  />
                ))}
              </div>
            </div>
          )}

          {/* N8n Workflows Section */}
          {toolsByType.n8n.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <span>⚡</span> N8n Workflow Automation
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {toolsByType.n8n.map((tool) => (
                  <ToolCard
                    key={tool.id}
                    tool={tool}
                    selected={selectedTool === tool.id}
                    onSelect={setSelectedTool}
                    onConnect={handleConnect}
                    onDisconnect={handleDisconnect}
                    onTest={handleTestConnection}
                    statusColors={statusColors}
                    formatLastSync={formatLastSync}
                  />
                ))}
              </div>
            </div>
          )}

          {/* MCP Servers Section */}
          {toolsByType.mcp.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <span>🧩</span> Model Context Protocol Servers
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {toolsByType.mcp.map((tool) => (
                  <ToolCard
                    key={tool.id}
                    tool={tool}
                    selected={selectedTool === tool.id}
                    onSelect={setSelectedTool}
                    onConnect={handleConnect}
                    onDisconnect={handleDisconnect}
                    onTest={handleTestConnection}
                    statusColors={statusColors}
                    formatLastSync={formatLastSync}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Other Integrations Section */}
          {toolsByType.integration.length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <span>🔗</span> Other Integrations
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {toolsByType.integration.map((tool) => (
                  <ToolCard
                    key={tool.id}
                    tool={tool}
                    selected={selectedTool === tool.id}
                    onSelect={setSelectedTool}
                    onConnect={handleConnect}
                    onDisconnect={handleDisconnect}
                    onTest={handleTestConnection}
                    statusColors={statusColors}
                    formatLastSync={formatLastSync}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add New Tool Button */}
      <div className="mt-8">
        <button className="w-full md:w-auto px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          + Add New MCP Server or Integration
        </button>
      </div>
    </div>
  );
}

// Tool Card Component
interface ToolCardProps {
  tool: MCPTool;
  selected: boolean;
  onSelect: (id: string) => void;
  onConnect: (id: string) => void;
  onDisconnect: (id: string) => void;
  onTest: (id: string) => void;
  statusColors: Record<string, string>;
  formatLastSync: (lastSync?: string) => string;
}

function ToolCard({
  tool,
  selected,
  onSelect,
  onConnect,
  onDisconnect,
  onTest,
  statusColors,
  formatLastSync,
}: ToolCardProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer ${
        selected ? "ring-2 ring-blue-500" : ""
      }`}
      onClick={() => onSelect(tool.id)}
    >
      {/* Tool Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{tool.icon}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
              {tool.name}
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
              {tool.type}
            </span>
          </div>
        </div>
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${statusColors[tool.status]}`}
        >
          {tool.status}
        </span>
      </div>

      {/* Tool Description */}
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{tool.description}</p>

      {/* Tool Metadata */}
      <div className="space-y-2 text-sm">
        {tool.metadata?.endpoint && (
          <div className="text-gray-500 dark:text-gray-400 truncate">
            <span className="font-medium">Endpoint:</span>{" "}
            <span className="text-xs">{tool.metadata.endpoint}</span>
          </div>
        )}
        <div className="flex justify-between text-gray-500 dark:text-gray-400">
          <span>Last Sync:</span>
          <span className="font-medium">{formatLastSync(tool.lastSync)}</span>
        </div>
        {tool.permissions.length > 0 && (
          <div className="text-gray-500 dark:text-gray-400">
            <span>Permissions: </span>
            <span className="font-medium">{tool.permissions.join(", ")}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex gap-2">
        {tool.status === "connected" ? (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTest(tool.id);
              }}
              className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Test
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDisconnect(tool.id);
              }}
              className="flex-1 px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Disconnect
            </button>
          </>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onConnect(tool.id);
            }}
            className="w-full px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
          >
            Connect
          </button>
        )}
      </div>
    </div>
  );
}
