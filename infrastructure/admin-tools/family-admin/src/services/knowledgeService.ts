import { Prompt, PromptStats, UserProfile, PromptAssemblyTest } from '@/types/knowledge';

const BASE_URL = '/api/phase2';

export const knowledgeService = {
  // --- Roles ---
  getRoles: async (): Promise<string[]> => {
    const response = await fetch(`${BASE_URL}/prompts/roles`);
    if (!response.ok) {
      throw new Error('Failed to fetch roles');
    }
    const data = await response.json();
    return data.roles;
  },

  getRolePrompt: async (role: string): Promise<Prompt> => {
    const response = await fetch(`${BASE_URL}/prompts/role/${role}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch role prompt: ${role}`);
    }
    return response.json();
  },

  saveRolePrompt: async (role: string, content: string): Promise<void> => {
    const response = await fetch(`${BASE_URL}/prompts/role/${role}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      throw new Error(`Failed to save role prompt: ${role}`);
    }
  },

  deleteRolePrompt: async (role: string): Promise<void> => {
    const response = await fetch(`${BASE_URL}/prompts/role/${role}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete role prompt: ${role}`);
    }
  },

  // --- Skills ---
  getSkills: async (): Promise<string[]> => {
    const response = await fetch(`${BASE_URL}/prompts/skills`);
    if (!response.ok) {
      throw new Error('Failed to fetch skills');
    }
    const data = await response.json();
    return data.skills;
  },

  getSkillPrompt: async (skill: string): Promise<Prompt> => {
    const response = await fetch(`${BASE_URL}/prompts/skill/${skill}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch skill prompt: ${skill}`);
    }
    return response.json();
  },

  saveSkillPrompt: async (skill: string, content: string): Promise<void> => {
    const response = await fetch(`${BASE_URL}/prompts/skill/${skill}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      throw new Error(`Failed to save skill prompt: ${skill}`);
    }
  },

  deleteSkillPrompt: async (skill: string): Promise<void> => {
    const response = await fetch(`${BASE_URL}/prompts/skill/${skill}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete skill prompt: ${skill}`);
    }
  },

  // --- User Assignment ---
  getUserProfile: async (userId: string): Promise<UserProfile> => {
    const response = await fetch(`${BASE_URL}/users/${userId}/profile`);
    if (!response.ok) {
      throw new Error(`Failed to fetch user profile: ${userId}`);
    }
    return response.json();
  },

  updateUserProfile: async (userId: string, data: Partial<UserProfile>): Promise<void> => {
    const response = await fetch(`${BASE_URL}/users/${userId}/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`Failed to update user profile: ${userId}`);
    }
  },

  // --- Testing ---
  testPromptAssembly: async (userId: string, role: string, language: string): Promise<PromptAssemblyTest> => {
    const params = new URLSearchParams({
      user_id: userId,
      role,
      language,
    });

    const response = await fetch(`${BASE_URL}/test/prompt-assembly?${params}`);
    if (!response.ok) {
      throw new Error('Failed to test prompt assembly');
    }
    return response.json();
  },
};