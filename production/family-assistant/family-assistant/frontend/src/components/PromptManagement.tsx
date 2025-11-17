/**
 * Prompt Management Component
 *
 * View, edit, and manage system prompts for different roles and contexts
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api-client';

interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  type: 'core' | 'role' | 'dynamic' | 'custom';
  role?: 'parent' | 'teenager' | 'child' | 'grandparent';
  content: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  version: number;
}

interface PromptBuildRequest {
  user_id?: string;
  role?: string;
  context?: string;
  custom_instructions?: string;
  language?: string;
}

interface BuiltPrompt {
  base_prompt: string;
  role_specific: string;
  context_specific: string;
  final_prompt: string;
  variables: Record<string, string>;
  metadata: {
    build_time: string;
    model_used: string;
    token_count: number;
  };
}

const PromptManagement: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptTemplate | null>(null);
  const [builtPrompt, setBuiltPrompt] = useState<BuiltPrompt | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'templates' | 'builder'>('templates');

  // Builder form state
  const [buildRequest, setBuildRequest] = useState<PromptBuildRequest>({
    user_id: '',
    role: 'parent',
    context: '',
    custom_instructions: '',
    language: 'en'
  });

  // Editor state
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    loadPromptTemplates();
  }, []);

  const loadPromptTemplates = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load core prompts
      const coreResponse = await apiClient.get('/phase2/prompts/core');
      const corePrompts = coreResponse.data.prompts || [];

      // Load role-specific prompts for all roles
      const roles = ['parent', 'teenager', 'child', 'grandparent'];
      const rolePrompts = [];

      for (const role of roles) {
        try {
          const roleResponse = await apiClient.get(`/phase2/prompts/role/${role}`);
          if (roleResponse.data) {
            rolePrompts.push({
              id: `role-${role}`,
              name: `${role.charAt(0).toUpperCase() + role.slice(1)} Role Prompt`,
              description: `Personality and behavior guidelines for ${role} role`,
              type: 'role' as const,
              role: role as any,
              content: roleResponse.data.content || '',
              variables: roleResponse.data.variables || [],
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              version: 1
            });
          }
        } catch (err) {
          console.warn(`Failed to load role prompt for ${role}:`, err);
        }
      }

      setPrompts([...corePrompts, ...rolePrompts]);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to load prompt templates';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const buildPrompt = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/phase2/prompts/build', buildRequest);
      setBuiltPrompt(response.data);
      setActiveTab('builder');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to build prompt';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromptSelect = (prompt: PromptTemplate) => {
    setSelectedPrompt(prompt);
    setEditContent(prompt.content);
    setIsEditing(false);
  };

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    if (isEditing && selectedPrompt) {
      // Discard changes
      setEditContent(selectedPrompt.content);
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedPrompt) return;

    setIsLoading(true);
    try {
      // TODO: Implement actual save endpoint
      // await apiClient.put(`/prompts/${selectedPrompt.id}`, {
      //   content: editContent
      // });

      // For now, just update local state
      setSelectedPrompt({
        ...selectedPrompt,
        content: editContent,
        updated_at: new Date().toISOString(),
        version: selectedPrompt.version + 1
      });

      setIsEditing(false);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to save prompt';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const getPromptIcon = (type: string) => {
    switch (type) {
      case 'core': return '⚙️';
      case 'role': return '🎭';
      case 'dynamic': return '🔄';
      case 'custom': return '✏️';
      default: return '📝';
    }
  };

  const getPromptBadgeColor = (type: string) => {
    switch (type) {
      case 'core': return 'bg-red-100 text-red-800';
      case 'role': return 'bg-blue-100 text-blue-800';
      case 'dynamic': return 'bg-green-100 text-green-800';
      case 'custom': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Prompt Management</h1>
        <p className="text-gray-600 mt-1">View and manage system prompts for different AI personalities</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('templates')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'templates'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Prompt Templates
          </button>
          <button
            onClick={() => setActiveTab('builder')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'builder'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Prompt Builder
          </button>
        </nav>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <span className="text-red-400">⚠️</span>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prompt List */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Templates</h2>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading templates...</p>
                </div>
              ) : prompts.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  No prompt templates found
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {prompts.map((prompt) => (
                    <div
                      key={prompt.id}
                      onClick={() => handlePromptSelect(prompt)}
                      className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedPrompt?.id === prompt.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">{getPromptIcon(prompt.type)}</span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPromptBadgeColor(prompt.type)}`}>
                          {prompt.type}
                        </span>
                        {prompt.is_active && (
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        )}
                      </div>
                      <h3 className="font-medium text-gray-900">{prompt.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{prompt.description}</p>
                      {prompt.role && (
                        <p className="text-xs text-gray-500 mt-1">Role: {prompt.role}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">Version {prompt.version}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Prompt Editor */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            {selectedPrompt ? (
              <div className="h-full flex flex-col">
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">
                      {selectedPrompt.name}
                    </h2>
                    <div className="flex items-center space-x-2">
                      {isEditing ? (
                        <>
                          <button
                            onClick={handleSaveEdit}
                            disabled={isLoading}
                            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            {isLoading ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            onClick={handleEditToggle}
                            className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={handleEditToggle}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex-1 p-6">
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Type:</span>
                        <span className="ml-2 text-gray-600">{selectedPrompt.type}</span>
                      </div>
                      {selectedPrompt.role && (
                        <div>
                          <span className="font-medium text-gray-700">Role:</span>
                          <span className="ml-2 text-gray-600">{selectedPrompt.role}</span>
                        </div>
                      )}
                      <div>
                        <span className="font-medium text-gray-700">Version:</span>
                        <span className="ml-2 text-gray-600">{selectedPrompt.version}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Updated:</span>
                        <span className="ml-2 text-gray-600">{formatDate(selectedPrompt.updated_at)}</span>
                      </div>
                    </div>

                    {selectedPrompt.variables.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Variables:</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedPrompt.variables.map((variable, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                            >
                              {'{'}{variable}{'}'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Content:</h3>
                      {isEditing ? (
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full h-64 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      ) : (
                        <div className="w-full h-64 p-3 bg-gray-50 rounded-lg overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-sm text-gray-900">
                            {selectedPrompt.content}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center p-6">
                <div className="text-center">
                  <div className="text-6xl mb-4">📝</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Template</h3>
                  <p className="text-gray-600">
                    Choose a prompt template from the list to view and edit its content
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Builder Tab */}
      {activeTab === 'builder' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Build Form */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Build Custom Prompt</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User ID
                </label>
                <input
                  type="text"
                  value={buildRequest.user_id}
                  onChange={(e) => setBuildRequest(prev => ({ ...prev, user_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Optional: Leave empty for general prompt"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <select
                  value={buildRequest.role}
                  onChange={(e) => setBuildRequest(prev => ({ ...prev, role: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="parent">Parent</option>
                  <option value="teenager">Teenager</option>
                  <option value="child">Child</option>
                  <option value="grandparent">Grandparent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Context
                </label>
                <textarea
                  value={buildRequest.context}
                  onChange={(e) => setBuildRequest(prev => ({ ...prev, context: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Current context or situation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Custom Instructions
                </label>
                <textarea
                  value={buildRequest.custom_instructions}
                  onChange={(e) => setBuildRequest(prev => ({ ...prev, custom_instructions: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Any additional instructions or constraints"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language
                </label>
                <select
                  value={buildRequest.language}
                  onChange={(e) => setBuildRequest(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>

              <button
                onClick={buildPrompt}
                disabled={isLoading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Building...' : 'Build Prompt'}
              </button>
            </div>
          </div>

          {/* Built Prompt Result */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Built Prompt</h2>
            {builtPrompt ? (
              <div className="space-y-4">
                {builtPrompt.metadata && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Metadata</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-medium">Build Time:</span>
                        <span className="ml-2 text-gray-600">
                          {formatDate(builtPrompt.metadata.build_time)}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">Token Count:</span>
                        <span className="ml-2 text-gray-600">
                          {builtPrompt.metadata.token_count}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Final Prompt</h3>
                  <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-900">
                      {builtPrompt.final_prompt}
                    </pre>
                  </div>
                </div>

                {Object.keys(builtPrompt.variables).length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Variables Used</h3>
                    <div className="space-y-1">
                      {Object.entries(builtPrompt.variables).map(([key, value]) => (
                        <div key={key} className="flex items-center space-x-2 text-sm">
                          <span className="font-medium text-gray-700">{key}:</span>
                          <span className="text-gray-600">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-96 text-center">
                <div>
                  <div className="text-6xl mb-4">🔧</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Prompt Built Yet</h3>
                  <p className="text-gray-600">
                    Configure the settings and click "Build Prompt" to generate a custom prompt
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PromptManagement;