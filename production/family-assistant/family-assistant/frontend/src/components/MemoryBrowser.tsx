/**
 * Memory Browser Component
 *
 * Browse and search through saved memories and conversations
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api-client';

interface MemorySearchResult {
  id: string;
  content: string;
  metadata: {
    user_id: string;
    conversation_id?: string;
    timestamp: string;
    memory_type: 'conversation' | 'context' | 'preference' | 'fact';
    relevance_score?: number;
    tags?: string[];
  };
}

interface MemoryStats {
  total_memories: number;
  conversation_memories: number;
  context_memories: number;
  preference_memories: number;
  fact_memories: number;
  last_updated: string;
}

const MemoryBrowser: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MemorySearchResult[]>([]);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<MemorySearchResult | null>(null);

  // Load memory stats on component mount
  useEffect(() => {
    loadMemoryStats();
  }, []);

  // Search memories when query changes (with debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        searchMemories(searchQuery);
      } else {
        setSearchResults([]);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadMemoryStats = async () => {
    try {
      const response = await apiClient.get('/phase2/stats');
      setMemoryStats(response.data);
    } catch (err) {
      console.error('Failed to load memory stats:', err);
      setError('Failed to load memory statistics');
    }
  };

  const searchMemories = async (query: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/phase2/memory/search', {
        query: query.trim(),
        limit: 20,
        user_id: null, // Search all memories for now
        memory_type: null, // Search all types
        date_range: null // Search all dates
      });

      setSearchResults(response.data.results || []);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to search memories';
      setError(message);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getMemoryIcon = (type: string) => {
    switch (type) {
      case 'conversation': return '💬';
      case 'context': return '🔄';
      case 'preference': return '⚙️';
      case 'fact': return '💡';
      default: return '📝';
    }
  };

  const getMemoryBadgeColor = (type: string) => {
    switch (type) {
      case 'conversation': return 'bg-blue-100 text-blue-800';
      case 'context': return 'bg-green-100 text-green-800';
      case 'preference': return 'bg-purple-100 text-purple-800';
      case 'fact': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleMemoryClick = (memory: MemorySearchResult) => {
    setSelectedMemory(memory);
  };

  const handleCloseDetail = () => {
    setSelectedMemory(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Memory Browser</h1>
        <p className="text-gray-600 mt-1">Search and browse through saved memories and conversations</p>
      </div>

      {/* Search Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search memories, conversations, facts..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="text-2xl">🔍</div>
        </div>

        {isLoading && (
          <div className="mt-4 flex items-center space-x-2 text-gray-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Searching memories...</span>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <span className="text-red-400">⚠️</span>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Memory Stats */}
      {memoryStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-center">
              <div className="text-2xl mb-2">📚</div>
              <p className="text-sm font-medium text-gray-600">Total Memories</p>
              <p className="text-xl font-bold text-gray-900">{memoryStats.total_memories}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-center">
              <div className="text-2xl mb-2">💬</div>
              <p className="text-sm font-medium text-gray-600">Conversations</p>
              <p className="text-xl font-bold text-gray-900">{memoryStats.conversation_memories}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-center">
              <div className="text-2xl mb-2">🔄</div>
              <p className="text-sm font-medium text-gray-600">Context</p>
              <p className="text-xl font-bold text-gray-900">{memoryStats.context_memories}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-center">
              <div className="text-2xl mb-2">⚙️</div>
              <p className="text-sm font-medium text-gray-600">Preferences</p>
              <p className="text-xl font-bold text-gray-900">{memoryStats.preference_memories}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-center">
              <div className="text-2xl mb-2">💡</div>
              <p className="text-sm font-medium text-gray-600">Facts</p>
              <p className="text-xl font-bold text-gray-900">{memoryStats.fact_memories}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Search Results ({searchResults.length})
            </h2>
          </div>

          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {searchResults.map((memory) => (
              <div
                key={memory.id}
                onClick={() => handleMemoryClick(memory)}
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex items-start space-x-3">
                  <div className="text-xl mt-1">{getMemoryIcon(memory.metadata.memory_type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getMemoryBadgeColor(memory.metadata.memory_type)}`}>
                        {memory.metadata.memory_type}
                      </span>
                      {memory.metadata.relevance_score && (
                        <span className="text-xs text-gray-500">
                          Score: {(memory.metadata.relevance_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900 line-clamp-2">
                      {memory.content}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>{formatDate(memory.metadata.timestamp)}</span>
                      {memory.metadata.conversation_id && (
                        <span>Conversation: {memory.metadata.conversation_id.slice(0, 8)}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!isLoading && searchQuery && searchResults.length === 0 && !error && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No memories found</h3>
          <p className="text-gray-600">
            Try searching with different keywords or check your spelling
          </p>
        </div>
      )}

      {/* Memory Detail Modal */}
      {selectedMemory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Memory Details</h3>
                <button
                  onClick={handleCloseDetail}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xl">{getMemoryIcon(selectedMemory.metadata.memory_type)}</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getMemoryBadgeColor(selectedMemory.metadata.memory_type)}`}>
                    {selectedMemory.metadata.memory_type}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Content</h4>
                  <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">{selectedMemory.content}</p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-gray-700">Timestamp</h4>
                    <p className="text-gray-600">{formatDate(selectedMemory.metadata.timestamp)}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700">User ID</h4>
                    <p className="text-gray-600">{selectedMemory.metadata.user_id}</p>
                  </div>
                </div>

                {selectedMemory.metadata.conversation_id && (
                  <div>
                    <h4 className="font-medium text-gray-700">Conversation ID</h4>
                    <p className="text-gray-600 font-mono">{selectedMemory.metadata.conversation_id}</p>
                  </div>
                )}

                {selectedMemory.metadata.tags && selectedMemory.metadata.tags.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Tags</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedMemory.metadata.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedMemory.metadata.relevance_score && (
                  <div>
                    <h4 className="font-medium text-gray-700">Relevance Score</h4>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${selectedMemory.metadata.relevance_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">
                        {(selectedMemory.metadata.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryBrowser;