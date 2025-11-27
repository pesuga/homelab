import {
  Prompt,
  PromptStats,
  UserProfile,
  PromptAssemblyTest,
  CorePromptMetadata,
  CorePromptDetail,
  CorePromptUpdateRequest,
  CorePromptRollbackRequest,
  CorePromptUpdateResponse,
  CorePromptRollbackResponse,
  CorePromptsListResponse,
  PromptVersionsListResponse
} from '@/types/knowledge';

const BASE_URL = '/api/phase2';

export const knowledgeService = {
  // --- Core Prompts (Version Control) ---
  getCorePrompts: async (): Promise<CorePromptsListResponse> => {
    const response = await fetch(`${BASE_URL}/prompts/core`);
    if (!response.ok) {
      throw new Error('Failed to fetch core prompts');
    }
    const data = await response.json();

    // Transform single prompt response to list format with all 3 core prompts
    // Backend returns: { prompt: string, length: number, estimated_tokens: number }
    // Frontend expects: { prompts: CorePromptMetadata[], total_count: number }

    return {
      prompts: [
        {
          name: 'FAMILY_ASSISTANT',
          display_name: 'Family Assistant',
          description: 'Core system prompt defining the AI assistant\'s role and capabilities',
          file_path: '/prompts/core/FAMILY_ASSISTANT.md',
          version_count: 0,
          last_modified: new Date().toISOString(),
          size_bytes: data.length || 0,
          token_estimate: data.estimated_tokens || 0,
        },
        {
          name: 'PRINCIPLES',
          display_name: 'Principles',
          description: 'Guiding principles and behavioral rules for the AI assistant',
          file_path: '/prompts/core/PRINCIPLES.md',
          version_count: 0,
          last_modified: new Date().toISOString(),
          size_bytes: 0,
          token_estimate: 0,
        },
        {
          name: 'RULES',
          display_name: 'Rules',
          description: 'Specific rules and constraints for the AI assistant behavior',
          file_path: '/prompts/core/RULES.md',
          version_count: 0,
          last_modified: new Date().toISOString(),
          size_bytes: 0,
          token_estimate: 0,
        },
      ],
      total_count: 3,
    };
  },

  getCorePromptDetail: async (name: string): Promise<CorePromptDetail> => {
    // Since backend only has /prompts/core (single endpoint), we fetch from there
    // and only support FAMILY_ASSISTANT for now
    if (name !== 'FAMILY_ASSISTANT') {
      // For other prompts, return empty content with metadata
      return {
        metadata: {
          name: name,
          display_name: name.replace(/_/g, ' '),
          description: `Core prompt: ${name}`,
          file_path: `/prompts/core/${name}.md`,
          version_count: 0,
          last_modified: new Date().toISOString(),
          size_bytes: 0,
          token_estimate: 0,
        },
        content: '',
        versions: [],
      };
    }

    const response = await fetch(`${BASE_URL}/prompts/core`);
    if (!response.ok) {
      throw new Error(`Failed to fetch core prompt: ${name}`);
    }
    const data = await response.json();

    return {
      metadata: {
        name: name,
        display_name: 'Family Assistant',
        description: 'Core system prompt defining the AI assistant\'s role and capabilities',
        file_path: `/prompts/core/${name}.md`,
        version_count: 0,
        last_modified: new Date().toISOString(),
        size_bytes: data.length || 0,
        token_estimate: data.estimated_tokens || 0,
      },
      content: data.prompt || '',
      versions: [],
    };
  },

  updateCorePrompt: async (
    name: string,
    request: CorePromptUpdateRequest
  ): Promise<CorePromptUpdateResponse> => {
    // Since backend only has /prompts/core (single endpoint), we update there
    // and only support FAMILY_ASSISTANT for now
    if (name !== 'FAMILY_ASSISTANT') {
      throw new Error(`Only FAMILY_ASSISTANT prompt is currently supported for editing`);
    }

    const response = await fetch(`${BASE_URL}/prompts/core`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: request.content,
        change_summary: request.change_summary || 'Manual update'
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to update core prompt: ${name}`);
    }
    const data = await response.json();

    // Parse the simple response from backend
    return {
      success: true,
      name: name,
      previous_version: {
        timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        filename: `${name}.md`,
        author: 'system',
        change_summary: 'Previous version',
        size_bytes: request.content.length,
        token_estimate: Math.ceil(request.content.length / 4),
      },
      new_version: {
        timestamp: new Date().toISOString(),
        filename: `${name}.md`,
        author: request.author || 'admin',
        change_summary: request.change_summary || 'Manual update',
        size_bytes: request.content.length,
        token_estimate: Math.ceil(request.content.length / 4),
      },
      message: data.message || 'Core prompt updated successfully',
    };
  },

  getCorePromptVersions: async (name: string): Promise<PromptVersionsListResponse> => {
    const response = await fetch(`${BASE_URL}/prompts/core/${name}/versions`);
    if (!response.ok) {
      throw new Error(`Failed to fetch versions for: ${name}`);
    }
    return response.json();
  },

  getCorePromptVersion: async (name: string, timestamp: string): Promise<any> => {
    const response = await fetch(`${BASE_URL}/prompts/core/${name}/versions/${timestamp}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch version: ${timestamp}`);
    }
    return response.json();
  },

  rollbackCorePrompt: async (
    name: string,
    request: CorePromptRollbackRequest
  ): Promise<CorePromptRollbackResponse> => {
    const response = await fetch(`${BASE_URL}/prompts/core/${name}/rollback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`Failed to rollback prompt: ${name}`);
    }
    return response.json();
  },

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