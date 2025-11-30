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
