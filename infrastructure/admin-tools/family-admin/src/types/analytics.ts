/**
 * Types for Sub-Agent Analytics Dashboard
 */

export interface AnalyticsOverview {
  metrics: {
    total_executions_24h: number;
    success_rate: number;
    avg_response_time_ms: number;
    total_tokens: number;
  };
  agent_popularity: Array<{
    agent: string;
    count: number;
  }>;
  recent_executions: Array<{
    execution_id: string;
    timestamp: string;
    agent: string;
    success: boolean;
    response_time_ms: number;
    total_tokens: number;
  }>;
}

/**
 * Chat Analytics Types (from Loki)
 */

export interface ChatLogEntry {
  timestamp: string;
  user_id: string;
  thread_id: string;
  session_id: string;
  tokens: number;
  latency_ms: number;
  cost_usd: number;
  model_used: string;
  error: boolean;
}

export interface ChatOverviewMetrics {
  total_requests: number;
  total_tokens: number;
  estimated_cost_usd: number;
  error_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  time_range: string;
}

export interface TokenStats {
  by_model: Record<string, number>;
  total: number;
  time_range: string;
}

export interface ExecutionTrace {
  execution_id: string;
  timestamp: string;
  user_query: string;

  intent_classification: {
    agent: string;
    confidence: number;
    keywords: string[];
    classification_time_ms: number;
  };

  agent_execution: {
    agent: string;
    prompt_size_chars: number;
    response_size_chars: number;
    execution_time_ms: number;
    success: boolean;
    error?: string;
  };

  tool_calls: Array<{
    tool_name: string;
    duration_ms: number;
    success: boolean;
    input_size: number;
    output_size: number;
    error?: string;
  }>;

  token_breakdown: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };

  timing_breakdown: {
    classification: number;
    agent_execution: number;
    tool_calls: number;
    total: number;
  };
}
