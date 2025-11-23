"use client";

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Prompt } from '@/types/knowledge';
import { useRolePrompt, useSaveRolePrompt, useDeleteRolePrompt, useSkillPrompt, useSaveSkillPrompt, useDeleteSkillPrompt } from '@/hooks/useKnowledge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Save, Trash2, X } from 'lucide-react';

interface PromptEditorProps {
  type: 'role' | 'skill';
  name: string;
  isOpen: boolean;
  onClose: () => void;
  isNew?: boolean;
}

export default function PromptEditor({ type, name, isOpen, onClose, isNew = false }: PromptEditorProps) {
  const [content, setContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const queryClient = useQueryClient();

  // Use the appropriate hook based on type
  const promptQuery = type === 'role'
    ? useRolePrompt(isNew ? '' : name)
    : useSkillPrompt(isNew ? '' : name);

  const saveRolePromptMutation = useSaveRolePrompt();
  const saveSkillPromptMutation = useSaveSkillPrompt();
  const deleteRolePromptMutation = useDeleteRolePrompt();
  const deleteSkillPromptMutation = useDeleteSkillPrompt();

  // Initialize content when data is loaded
  if (!isNew && promptQuery.data && !hasChanges) {
    setContent(promptQuery.data.content);
  }

  const handleSave = async () => {
    if (isNew) {
      // For new prompts, we'll handle the naming in the parent component
      // This is a simplified approach - in practice, you might want a separate flow
      onClose();
      return;
    }

    const mutation = type === 'role'
      ? saveRolePromptMutation.mutateAsync({ role: name, content })
      : saveSkillPromptMutation.mutateAsync({ skill: name, content });

    try {
      await mutation;
      setHasChanges(false);
      onClose();
    } catch (error) {
      console.error('Failed to save prompt:', error);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) {
      return;
    }

    const mutation = type === 'role'
      ? deleteRolePromptMutation.mutateAsync({ role: name })
      : deleteSkillPromptMutation.mutateAsync({ skill: name });

    try {
      await mutation;
      onClose();
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    }
  };

  const isLoading = promptQuery.isLoading || (type === 'role' ? saveRolePromptMutation.isPending : saveSkillPromptMutation.isPending) || (type === 'role' ? deleteRolePromptMutation.isPending : deleteSkillPromptMutation.isPending);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isNew ? `Create New ${type === 'role' ? 'Role' : 'Skill'}` : `Edit ${type === 'role' ? 'Role' : 'Skill'}: ${name}`}
          </DialogTitle>
          <DialogDescription>
            {isNew
              ? `Create a new ${type} prompt with markdown content.`
              : `Edit the markdown content for this ${type}. Changes will be saved immediately.`
            }
          </DialogDescription>
        </DialogHeader>

        {promptQuery.error && (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to load {type} prompt: {(promptQuery.error as Error).message}
            </AlertDescription>
          </Alert>
        )}

        {(type === 'role' ? saveRolePromptMutation.error : saveSkillPromptMutation.error) && (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to save {type} prompt: {((type === 'role' ? saveRolePromptMutation.error : saveSkillPromptMutation.error) as Error)?.message || 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {!isNew && (
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {type === 'role' ? 'Role' : 'Skill'} Name
              </label>
              <Input value={name} disabled className="mt-1" />
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Content (Markdown)
            </label>
            <Textarea
              value={content}
              onChange={(e) => {
                setContent(e.target.value);
                setHasChanges(true);
              }}
              placeholder={`Enter the ${type} prompt content in markdown format...`}
              className="mt-1 min-h-[400px] font-mono text-sm"
              disabled={isLoading}
            />
          </div>

          {promptQuery.data && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Length: {promptQuery.data.length} characters |
              Estimated tokens: {promptQuery.data.estimated_tokens}
            </div>
          )}
        </div>

        <DialogFooter className="flex justify-between">
          <div className="flex space-x-2">
            {!isNew && (
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isLoading}
              >
                {(type === 'role' ? deleteRolePromptMutation.isPending : deleteSkillPromptMutation.isPending) ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </Button>
            )}
          </div>

          <div className="flex space-x-2">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isLoading || (!hasChanges && !isNew)}>
              {(type === 'role' ? saveRolePromptMutation.isPending : saveSkillPromptMutation.isPending) ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {isNew ? 'Create' : 'Save'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}