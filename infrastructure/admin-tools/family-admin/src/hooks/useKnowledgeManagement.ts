/**
 * Knowledge Management Hook
 *
 * Manages MD documents that customize the system prompt for the entire family.
 * These documents serve as first-layer memory that's always present in conversations.
 */

import { useState, useEffect, useCallback } from 'react';

export interface KnowledgeDocument {
  id: string;
  title: string;
  content: string;
  category: 'family-rules' | 'preferences' | 'routines' | 'important-info' | 'custom';
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  author: string;
  word_count: number;
}

export interface KnowledgeStats {
  total_documents: number;
  active_documents: number;
  total_words: number;
  categories: Record<string, number>;
  last_updated: string;
}

interface UseKnowledgeManagementReturn {
  // Data
  documents: KnowledgeDocument[];
  stats: KnowledgeStats | null;
  loading: boolean;
  error: string | null;

  // Form state
  editingDocument: KnowledgeDocument | null;
  isCreating: boolean;

  // Operations
  fetchDocuments: () => Promise<void>;
  createDocument: (document: Partial<KnowledgeDocument>) => Promise<void>;
  updateDocument: (id: string, updates: Partial<KnowledgeDocument>) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  toggleDocumentActive: (id: string) => Promise<void>;

  // Form handlers
  startEdit: (document: KnowledgeDocument) => void;
  startCreate: () => void;
  cancelEdit: () => void;
  saveDocument: (document: Partial<KnowledgeDocument>) => Promise<void>;

  // Utility
  refreshStats: () => Promise<void>;
}

const CATEGORIES = [
  { value: 'family-rules', label: 'Family Rules', description: 'House rules and guidelines' },
  { value: 'preferences', label: 'Preferences', description: 'Family preferences and likes' },
  { value: 'routines', label: 'Routines', description: 'Daily routines and schedules' },
  { value: 'important-info', label: 'Important Info', description: 'Critical family information' },
  { value: 'custom', label: 'Custom', description: 'Custom knowledge documents' }
];

export function useKnowledgeManagement(): UseKnowledgeManagementReturn {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingDocument, setEditingDocument] = useState<KnowledgeDocument | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Mock data generator for demonstration
  const generateMockDocuments = (): KnowledgeDocument[] => [
    {
      id: '1',
      title: 'House Rules',
      content: `# House Rules

## Screen Time
- No screens during dinner time
- Homework must be finished before recreational screen time
- Bedtime: 9 PM for kids, 10 PM for teens

## Chores
- Everyone helps with dinner cleanup
- Saturday morning: room cleaning
- Take out trash when full

## Manners
- Say please and thank you
- Look people in the eye when talking
- Respect each other's belongings`,
      category: 'family-rules',
      tags: ['rules', 'daily-life', 'chores'],
      is_active: true,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-18T14:30:00Z',
      author: 'Mom',
      word_count: 85
    },
    {
      id: '2',
      title: 'Family Preferences',
      content: `# Family Preferences

## Food Preferences
- Pizza night: Every Friday
- No spicy food for the little ones
- Dad loves spicy food
- Everyone likes pasta

## Activities
- Weekend hikes when weather is nice
- Movie night on Saturdays
- Board games on rainy days

## Holidays
- Christmas: Grandparents visit
- Summer vacation: Beach trip
- Birthday traditions: Choice of dinner restaurant`,
      category: 'preferences',
      tags: ['preferences', 'food', 'activities'],
      is_active: true,
      created_at: '2025-01-10T16:20:00Z',
      updated_at: '2025-01-16T09:15:00Z',
      author: 'Dad',
      word_count: 72
    },
    {
      id: '3',
      title: 'Morning Routine',
      content: `# Morning Routine

## School Days
- 6:30 AM: Wake up
- 7:00 AM: Breakfast
- 7:30 AM: Get dressed
- 8:00 AM: Leave for school

## Weekends
- 8:00 AM: Wake up
- 9:00 AM: Family breakfast
- 10:00 AM: Chores and activities

## Reminders
- Pack lunch the night before
- Check backpack before leaving
- Brush teeth and hair`,
      category: 'routines',
      tags: ['morning', 'school', 'routine'],
      is_active: true,
      created_at: '2025-01-08T12:45:00Z',
      updated_at: '2025-01-12T11:20:00Z',
      author: 'Mom',
      word_count: 58
    }
  ];

  const generateMockStats = (): KnowledgeStats => {
    const docs = generateMockDocuments();
    const activeDocs = docs.filter(doc => doc.is_active);
    const categoryCounts = docs.reduce((acc, doc) => {
      acc[doc.category] = (acc[doc.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total_documents: docs.length,
      active_documents: activeDocs.length,
      total_words: docs.reduce((sum, doc) => sum + doc.word_count, 0),
      categories: categoryCounts,
      last_updated: new Date().toISOString()
    };
  };

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Simulate API call - replace with actual API when available
      await new Promise(resolve => setTimeout(resolve, 500));
      const mockDocs = generateMockDocuments();
      setDocuments(mockDocs);
    } catch (error) {
      setError('Failed to fetch knowledge documents');
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create document
  const createDocument = useCallback(async (document: Partial<KnowledgeDocument>) => {
    setLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));

      const newDoc: KnowledgeDocument = {
        id: Date.now().toString(),
        title: document.title || 'Untitled Document',
        content: document.content || '',
        category: document.category || 'custom',
        tags: document.tags || [],
        is_active: document.is_active ?? true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        author: 'Admin',
        word_count: document.content?.split(/\s+/).length || 0
      };

      setDocuments(prev => [...prev, newDoc]);
      await refreshStats();
    } catch (error) {
      setError('Failed to create document');
      console.error('Error creating document:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Update document
  const updateDocument = useCallback(async (id: string, updates: Partial<KnowledgeDocument>) => {
    setLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));

      setDocuments(prev => prev.map(doc => {
        if (doc.id === id) {
          return {
            ...doc,
            ...updates,
            updated_at: new Date().toISOString(),
            word_count: updates.content ? updates.content.split(/\s+/).length : doc.word_count
          };
        }
        return doc;
      }));

      await refreshStats();
    } catch (error) {
      setError('Failed to update document');
      console.error('Error updating document:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete document
  const deleteDocument = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));

      setDocuments(prev => prev.filter(doc => doc.id !== id));
      await refreshStats();
    } catch (error) {
      setError('Failed to delete document');
      console.error('Error deleting document:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Toggle document active status
  const toggleDocumentActive = useCallback(async (id: string) => {
    const document = documents.find(doc => doc.id === id);
    if (document) {
      await updateDocument(id, { is_active: !document.is_active });
    }
  }, [documents, updateDocument]);

  // Refresh stats
  const refreshStats = useCallback(async () => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 200));
      setStats(generateMockStats());
    } catch (error) {
      console.error('Error refreshing stats:', error);
    }
  }, []);

  // Form handlers
  const startEdit = useCallback((document: KnowledgeDocument) => {
    setEditingDocument(document);
    setIsCreating(false);
  }, []);

  const startCreate = useCallback(() => {
    setEditingDocument(null);
    setIsCreating(true);
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingDocument(null);
    setIsCreating(false);
  }, []);

  const saveDocument = useCallback(async (document: Partial<KnowledgeDocument>) => {
    if (isCreating) {
      await createDocument(document);
    } else if (editingDocument) {
      await updateDocument(editingDocument.id, document);
    }
    cancelEdit();
  }, [isCreating, editingDocument, createDocument, updateDocument, cancelEdit]);

  // Initial load
  useEffect(() => {
    fetchDocuments();
    refreshStats();
  }, [fetchDocuments, refreshStats]);

  return {
    documents,
    stats,
    loading,
    error,
    editingDocument,
    isCreating,
    fetchDocuments,
    createDocument,
    updateDocument,
    deleteDocument,
    toggleDocumentActive,
    startEdit,
    startCreate,
    cancelEdit,
    saveDocument,
    refreshStats,
    CATEGORIES
  };
}