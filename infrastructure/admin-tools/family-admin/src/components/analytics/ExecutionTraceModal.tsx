/**
 * Execution Trace Modal Component
 * Displays detailed execution trace with timeline visualization
 */

import React from 'react';
import { ExecutionTrace } from '@/types/analytics';

interface ExecutionTraceModalProps {
  trace: ExecutionTrace | null;
  onClose: () => void;
}

export default function ExecutionTraceModal({ trace, onClose }: ExecutionTraceModalProps) {
  if (!trace) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
              Execution Trace
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {new Date(trace.timestamp).toLocaleString()} • {trace.execution_id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* User Query */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">User Query</p>
            <p className="text-gray-700 dark:text-gray-300">{trace.user_query}</p>
          </div>

          {/* Timeline Visualization */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Execution Timeline</h3>

            {/* Timeline bars */}
            <div className="space-y-3">
              <TimelineBar
                label="Intent Classification"
                duration={trace.timing_breakdown.classification}
                color="bg-purple-500"
              />
              <TimelineBar
                label="Agent Execution"
                duration={trace.timing_breakdown.agent_execution}
                color="bg-blue-500"
              />
              <TimelineBar
                label="Tool Calls"
                duration={trace.timing_breakdown.tool_calls}
                color="bg-green-500"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-700 rounded">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Total Duration</span>
              <span className="text-lg font-bold text-gray-800 dark:text-white">
                {trace.timing_breakdown.total.toFixed(0)}ms
              </span>
            </div>
          </div>

          {/* Intent Classification */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
              Intent Classification
            </h3>
            <div className="space-y-2">
              <InfoRow label="Agent" value={trace.intent_classification.agent} />
              <InfoRow
                label="Confidence"
                value={`${(trace.intent_classification.confidence * 100).toFixed(1)}%`}
              />
              <div className="flex items-start justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Keywords</span>
                <div className="flex flex-wrap gap-1 justify-end max-w-md">
                  {trace.intent_classification.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Agent Execution */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
              Agent Execution
            </h3>
            <div className="space-y-2">
              <InfoRow label="Agent" value={trace.agent_execution.agent} />
              <InfoRow
                label="Prompt Size"
                value={`${trace.agent_execution.prompt_size_chars.toLocaleString()} chars`}
              />
              <InfoRow
                label="Response Size"
                value={`${trace.agent_execution.response_size_chars.toLocaleString()} chars`}
              />
              <InfoRow
                label="Duration"
                value={`${trace.agent_execution.execution_time_ms.toFixed(0)}ms`}
              />
              <InfoRow
                label="Status"
                value={
                  <span className={`px-2 py-1 text-xs rounded ${
                    trace.agent_execution.success
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                      : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                  }`}>
                    {trace.agent_execution.success ? 'Success' : 'Failed'}
                  </span>
                }
              />
              {trace.agent_execution.error && (
                <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-800 dark:text-red-300">
                  {trace.agent_execution.error}
                </div>
              )}
            </div>
          </div>

          {/* Tool Calls */}
          {trace.tool_calls.length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
                Tool Calls ({trace.tool_calls.length})
              </h3>
              <div className="space-y-2">
                {trace.tool_calls.map((tool, idx) => (
                  <details key={idx} className="group">
                    <summary className="cursor-pointer p-3 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-800 dark:text-white">
                            {tool.tool_name}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            tool.success
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                              : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                          }`}>
                            {tool.success ? 'Success' : 'Failed'}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {tool.duration_ms.toFixed(0)}ms
                        </span>
                      </div>
                    </summary>
                    <div className="mt-2 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded">
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Input Size</span>
                          <span className="text-gray-800 dark:text-white">{tool.input_size} bytes</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Output Size</span>
                          <span className="text-gray-800 dark:text-white">{tool.output_size} bytes</span>
                        </div>
                        {tool.error && (
                          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-300">
                            {tool.error}
                          </div>
                        )}
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            </div>
          )}

          {/* Token Breakdown */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">
              Token Breakdown
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 text-gray-600 dark:text-gray-400">Metric</th>
                    <th className="text-right py-2 text-gray-600 dark:text-gray-400">Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 text-gray-700 dark:text-gray-300">Prompt Tokens</td>
                    <td className="py-2 text-right text-gray-800 dark:text-white font-medium">
                      {trace.token_breakdown.prompt_tokens.toLocaleString()}
                    </td>
                  </tr>
                  <tr className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 text-gray-700 dark:text-gray-300">Completion Tokens</td>
                    <td className="py-2 text-right text-gray-800 dark:text-white font-medium">
                      {trace.token_breakdown.completion_tokens.toLocaleString()}
                    </td>
                  </tr>
                  <tr className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 text-gray-700 dark:text-gray-300 font-semibold">Total Tokens</td>
                    <td className="py-2 text-right text-gray-800 dark:text-white font-semibold">
                      {trace.token_breakdown.total_tokens.toLocaleString()}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-700 dark:text-gray-300">Estimated Cost</td>
                    <td className="py-2 text-right text-gray-800 dark:text-white font-medium">
                      ${trace.token_breakdown.estimated_cost_usd.toFixed(4)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function TimelineBar({ label, duration, color }: { label: string; duration: number; color: string }) {
  // Calculate percentage (max 100%)
  const maxDuration = 5000; // 5 seconds max for visualization
  const percentage = Math.min((duration / maxDuration) * 100, 100);

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
        <span className="text-sm font-medium text-gray-800 dark:text-white">{duration.toFixed(0)}ms</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          className={`${color} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-1">
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      <span className="text-sm text-gray-800 dark:text-white font-medium text-right">
        {value}
      </span>
    </div>
  );
}
