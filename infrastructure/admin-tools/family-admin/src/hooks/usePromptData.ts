/**
 * Custom hook for managing Phase 2 prompt system
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, PromptResponse, PromptBuildRequest } from '@/lib/api-client';

interface UsePromptDataReturn {
  // Prompt data
  corePrompt: PromptResponse | null;
  rolePrompts: Record<string, PromptResponse>;
  builtPrompt: PromptResponse | null;
  loading: boolean;
  error: string | null;

  // Operations
  getCorePrompt: () => Promise<void>;
  getRolePrompt: (role: string) => Promise<void>;
  buildPrompt: (userId: string, options?: PromptBuildRequest) => Promise<void>;

  // Available roles
  availableRoles: string[];
}

const FAMILY_ROLES = ['parent', 'teenager', 'child', 'grandparent', 'member'];

export function usePromptData(): UsePromptDataReturn {
  const [corePrompt, setCorePrompt] = useState<PromptResponse | null>(null);
  const [rolePrompts, setRolePrompts] = useState<Record<string, PromptResponse>>({});
  const [builtPrompt, setBuiltPrompt] = useState<PromptResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get core system prompt
  const getCorePrompt = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const prompt = await apiClient.getCorePrompt();
      setCorePrompt(prompt);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch core prompt';
      setError(message);
      console.error('Error fetching core prompt:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Get role-specific prompt
  const getRolePrompt = useCallback(async (role: string) => {
    setLoading(true);
    setError(null);
    try {
      const prompt = await apiClient.getRolePrompt(role);
      setRolePrompts(prev => ({
        ...prev,
        [role]: prompt
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : `Failed to fetch ${role} prompt`;
      setError(message);
      console.error('Error fetching role prompt:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Build dynamic prompt for user
  const buildPrompt = useCallback(async (userId: string, options: Partial<PromptBuildRequest> = {}) => {
    setLoading(true);
    setError(null);
    try {
      const buildRequest: PromptBuildRequest = {
        user_id: userId,
        conversation_id: options.conversation_id || 'admin-session',
        minimal: options.minimal || false,
        ...options
      };
      const prompt = await apiClient.buildPrompt(buildRequest);
      setBuiltPrompt(prompt);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to build prompt';
      setError(message);
      console.error('Error building prompt:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load core prompt on mount
  useEffect(() => {
    getCorePrompt();
  }, [getCorePrompt]);

  // Load all role prompts
  useEffect(() => {
    FAMILY_ROLES.forEach(role => {
      getRolePrompt(role);
    });
  }, [getRolePrompt]);

  return {
    corePrompt,
    rolePrompts,
    builtPrompt,
    loading,
    error,
    getCorePrompt,
    getRolePrompt,
    buildPrompt,
    availableRoles: FAMILY_ROLES,
  };
}