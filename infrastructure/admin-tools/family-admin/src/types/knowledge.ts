export interface Prompt {
  name: string; // role or skill name
  content: string;
  length: number;
  estimated_tokens: number;
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