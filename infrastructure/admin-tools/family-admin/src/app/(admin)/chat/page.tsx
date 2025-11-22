"use client";

import React, { useState } from "react";
import { usePromptData } from "@/hooks/usePromptData";

export default function PromptManager() {
  const [selectedRole, setSelectedRole] = useState<string>("parent");
  const [userId, setUserId] = useState<string>("admin-user");
  const [conversationId, setConversationId] = useState<string>("admin-session");
  const [minimalMode, setMinimalMode] = useState<boolean>(false);

  const {
    corePrompt,
    rolePrompts,
    builtPrompt,
    loading,
    error,
    getCorePrompt,
    getRolePrompt,
    buildPrompt,
    availableRoles,
  } = usePromptData();

  const handleBuildPrompt = () => {
    buildPrompt(userId, {
      conversation_id: conversationId,
      minimal: minimalMode,
    });
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getPromptStats = (prompt: any) => {
    if (!prompt) return null;
    return {
      length: prompt.prompt?.length || 0,
      tokens: prompt.estimated_tokens || 0,
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            System Prompt Manager
          </h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Manage and test Phase 2 dynamic prompt building system
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 text-red-800 dark:text-red-400 rounded">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Prompt Controls */}
        <div className="space-y-6">
          {/* Core System Prompt */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Core System Prompt
              </h3>
              <button
                onClick={getCorePrompt}
                disabled={loading}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 disabled:opacity-50"
              >
                {loading ? "Loading..." : "Refresh"}
              </button>
            </div>
            {corePrompt ? (
              <div>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
                  <span>Length: {corePrompt.length.toLocaleString()} chars</span>
                  <span>Tokens: ~{corePrompt.estimated_tokens.toLocaleString()}</span>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 max-h-60 overflow-y-auto">
                  <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">
                    {corePrompt.prompt.slice(0, 500)}
                    {corePrompt.prompt.length > 500 && "..."}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                Loading core prompt...
              </div>
            )}
          </div>

          {/* Role-Specific Prompts */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Role-Specific Prompts
            </h3>
            <div className="space-y-4">
              {availableRoles.map((role) => (
                <div key={role} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <button
                      onClick={() => getRolePrompt(role)}
                      className={`text-left flex-1 font-medium capitalize ${
                        selectedRole === role
                          ? "text-blue-600 dark:text-blue-400"
                          : "text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
                      }`}
                      onClick={() => setSelectedRole(role)}
                    >
                      {role} Role
                    </button>
                    {rolePrompts[role] && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {rolePrompts[role].estimated_tokens} tokens
                      </span>
                    )}
                  </div>
                  {selectedRole === role && rolePrompts[role] && (
                    <div className="mt-3 bg-gray-50 dark:bg-gray-700/50 rounded p-3 max-h-40 overflow-y-auto">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {rolePrompts[role].prompt.slice(0, 300)}
                        {rolePrompts[role].prompt.length > 300 && "..."}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Dynamic Prompt Builder */}
        <div className="space-y-6">
          {/* Prompt Builder */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Dynamic Prompt Builder
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter user ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Conversation ID
                </label>
                <input
                  type="text"
                  value={conversationId}
                  onChange={(e) => setConversationId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter conversation ID"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="minimal"
                  checked={minimalMode}
                  onChange={(e) => setMinimalMode(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="minimal" className="text-sm text-gray-700 dark:text-gray-300">
                  Minimal mode (reduce prompt size)
                </label>
              </div>

              <button
                onClick={handleBuildPrompt}
                disabled={loading || !userId}
                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Building..." : "Build Dynamic Prompt"}
              </button>
            </div>

            {builtPrompt && (
              <div className="mt-6 border-t border-gray-200 dark:border-gray-600 pt-6">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                  Generated Prompt
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <span>Role: <span className="font-medium capitalize">{builtPrompt.metadata?.role}</span></span>
                    <span>Language: <span className="font-medium">{builtPrompt.metadata?.language}</span></span>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 max-h-80 overflow-y-auto">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">
                      {builtPrompt.system_prompt}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* System Info */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              System Information
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Roles Available</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {availableRoles.length}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-600 dark:text-gray-400">Core Prompt Size</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {corePrompt ? `${corePrompt.estimated_tokens.toLocaleString()} tokens` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-600 dark:text-gray-400">Loaded Role Prompts</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {Object.keys(rolePrompts).length}/{availableRoles.length}
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">System Status</span>
                <span className="text-sm font-medium text-green-600 dark:text-green-400">
                  Active
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}