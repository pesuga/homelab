/**
 * Custom hook for managing knowledge base data with Phase 2 backend integration
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, KnowledgeItem } from '@/lib/api-client';

interface UseKnowledgeDataReturn {
  // Knowledge items
  items: KnowledgeItem[];
  loading: boolean;
  error: string | null;

  // Operations
  fetchItems: (category?: string) => Promise<void>;
  searchItems: (query: string) => Promise<void>;
  createItem: (item: Partial<KnowledgeItem>) => Promise<void>;
  updateItem: (id: string, updates: Partial<KnowledgeItem>) => Promise<void>;
  deleteItem: (id: string) => Promise<void>;

  // Search state
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isSearching: boolean;
}

export function useKnowledgeData(): UseKnowledgeDataReturn {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Fetch all items or by category
  const fetchItems = useCallback(async (category?: string) => {
    setLoading(true);
    setError(null);
    setIsSearching(false);
    try {
      const data = await apiClient.getKnowledgeItems(category);
      setItems(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch knowledge items';
      setError(message);
      console.error('Error fetching knowledge items:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Search knowledge base
  const searchItems = useCallback(async (query: string) => {
    if (!query.trim()) {
      fetchItems();
      return;
    }

    setLoading(true);
    setError(null);
    setIsSearching(true);
    try {
      const data = await apiClient.searchKnowledge(query);
      setItems(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to search knowledge';
      setError(message);
      console.error('Error searching knowledge:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchItems]);

  // Create new knowledge item
  const createItem = useCallback(async (item: Partial<KnowledgeItem>) => {
    setLoading(true);
    setError(null);
    try {
      const newItem = await apiClient.createKnowledgeItem(item);
      setItems(prev => [newItem, ...prev]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create knowledge item';
      setError(message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update existing knowledge item
  const updateItem = useCallback(async (id: string, updates: Partial<KnowledgeItem>) => {
    setLoading(true);
    setError(null);
    try {
      const updatedItem = await apiClient.updateKnowledgeItem(id, updates);
      setItems(prev => prev.map(item => item.id === id ? updatedItem : item));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update knowledge item';
      setError(message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete knowledge item
  const deleteItem = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.deleteKnowledgeItem(id);
      setItems(prev => prev.filter(item => item.id !== id));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete knowledge item';
      setError(message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  return {
    items,
    loading,
    error,
    fetchItems,
    searchItems,
    createItem,
    updateItem,
    deleteItem,
    searchQuery,
    setSearchQuery,
    isSearching,
  };
}
