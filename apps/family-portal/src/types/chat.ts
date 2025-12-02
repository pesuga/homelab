export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
  metadata?: {
    user_id?: string;
    session_id?: string;
    content_type?: 'text' | 'image' | 'audio' | 'document';
    [key: string]: any;
  };
}

export interface ChatRequest {
  message: string;
  user_id?: string;
  session_id?: string;
  content_type?: 'text' | 'image' | 'audio' | 'document';
  metadata?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  session_id?: string;
  metadata?: Record<string, any>;
}

export interface ChatError {
  error: string;
  details?: string;
  status?: number;
}
