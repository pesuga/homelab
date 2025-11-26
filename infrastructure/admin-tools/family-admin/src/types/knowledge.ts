export interface Prompt {
  name: string; // role or skill name
  content: string;
  length: number;
  estimated_tokens: number;
  type?: 'role' | 'skill' | 'core';
}

export interface PromptStats {
  total_length: number;
  estimated_tokens: number;
  section_count: number;
  has_memory_context: boolean;
  has_language_context: boolean;
  has_skills: boolean;
}

export interface UserProfile {
  user_id: string;
  role: string;
  age_group?: string;
  language_preference: 'en' | 'es' | 'bilingual';
  active_skills: string[];
  preferences: Record<string, any>;
}

export interface PromptAssemblyTest {
  full_prompt: string;
  token_reduction: {
    original: number;
    compressed: number;
    savings_percent: number;
  };
}

// ==============================================================================
// Core Prompt Types (Version Control)
// ==============================================================================

export interface PromptVersion {
  timestamp: string;
  filename: string;
  author: string;
  change_summary: string;
  size_bytes: number;
  token_estimate: number;
}

export interface CorePromptMetadata {
  name: string;
  display_name: string;
  description: string;
  file_path: string;
  current_version?: PromptVersion;
  version_count: number;
  last_modified?: string;
  size_bytes: number;
  token_estimate: number;
}

export interface CorePromptDetail {
  metadata: CorePromptMetadata;
  content: string;
  versions: PromptVersion[];
}

// ==============================================================================
// Request Types
// ==============================================================================

export interface CorePromptUpdateRequest {
  content: string;
  change_summary: string;
  author?: string;
}

export interface CorePromptRollbackRequest {
  version_timestamp: string;
  reason: string;
  author?: string;
}

// ==============================================================================
// Response Types
// ==============================================================================

export interface CorePromptUpdateResponse {
  success: boolean;
  name: string;
  previous_version: PromptVersion;
  new_version: PromptVersion;
  message: string;
}

export interface CorePromptRollbackResponse {
  success: boolean;
  name: string;
  restored_version: PromptVersion;
  backup_version: PromptVersion;
  message: string;
}

export interface CorePromptsListResponse {
  prompts: CorePromptMetadata[];
  total_count: number;
}

export interface PromptVersionsListResponse {
  name: string;
  versions: PromptVersion[];
  total_count: number;
}