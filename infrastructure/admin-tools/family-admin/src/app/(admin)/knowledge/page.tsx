"use client";

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRoles, useSkills } from '@/hooks/useKnowledge';
import PromptEditor from '@/components/knowledge/PromptEditor';
import PromptTester from '@/components/knowledge/PromptTester';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Loader2, Plus, Edit, Trash2, Users, Zap } from 'lucide-react';

export default function KnowledgePage() {
  const [selectedPrompt, setSelectedPrompt] = useState<{ type: 'role' | 'skill'; name: string } | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isNewPromptOpen, setIsNewPromptOpen] = useState(false);
  const [newPromptType, setNewPromptType] = useState<'role' | 'skill'>('role');
  const [newPromptName, setNewPromptName] = useState('');

  const { data: roles, isLoading: rolesLoading, error: rolesError } = useRoles();
  const { data: skills, isLoading: skillsLoading, error: skillsError } = useSkills();

  const handleEditPrompt = (type: 'role' | 'skill', name: string) => {
    setSelectedPrompt({ type, name });
    setIsEditorOpen(true);
  };

  const handleNewPrompt = (type: 'role' | 'skill') => {
    setNewPromptType(type);
    setNewPromptName('');
    setIsNewPromptOpen(true);
  };

  const handleCreateNewPrompt = () => {
    if (!newPromptName.trim()) return;

    // Close the dialog and open the editor with the new name
    setIsNewPromptOpen(false);
    setSelectedPrompt({ type: newPromptType, name: newPromptName.trim() });
    setIsEditorOpen(true);
  };

  const PromptList = ({ type, prompts, isLoading, error }: {
    type: 'role' | 'skill';
    prompts: string[] | undefined;
    isLoading: boolean;
    error: Error | null;
  }) => {
    const icon = type === 'role' ? <Users className="h-4 w-4" /> : <Zap className="h-4 w-4" />;
    const title = type === 'role' ? 'Roles' : 'Skills';
    const description = type === 'role'
      ? 'User roles like parent, child, teenager, etc.'
      : 'Specialized skills like calendar assistant, coding tutor, etc.';

    if (error) {
      return (
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load {type}s: {error.message}
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {icon}
              <CardTitle>{title}</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleNewPrompt(type)}
              disabled={isLoading}
            >
              <Plus className="h-4 w-4 mr-2" />
              New {type.slice(0, -1)}
            </Button>
          </div>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading {type}s...</span>
            </div>
          ) : prompts && prompts.length > 0 ? (
            <div className="grid gap-3">
              {prompts.map((prompt) => (
                <div
                  key={prompt}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <Badge variant={type === 'role' ? 'default' : 'secondary'}>
                      {type.slice(0, -1).toUpperCase()}
                    </Badge>
                    <span className="font-medium">{prompt}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditPrompt(type, prompt)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No {type}s found. Create your first {type} to get started.
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Knowledge Base</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage roles and skills that define how family members interact with the AI assistant.
        </p>
      </div>

      <Tabs defaultValue="roles" className="space-y-6">
        <TabsList>
          <TabsTrigger value="roles">Roles</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
          <TabsTrigger value="tester">Prompt Tester</TabsTrigger>
        </TabsList>

        <TabsContent value="roles">
          <PromptList
            type="role"
            prompts={roles}
            isLoading={rolesLoading}
            error={rolesError as Error | null}
          />
        </TabsContent>

        <TabsContent value="skills">
          <PromptList
            type="skill"
            prompts={skills}
            isLoading={skillsLoading}
            error={skillsError as Error | null}
          />
        </TabsContent>

        <TabsContent value="tester">
          <PromptTester />
        </TabsContent>
      </Tabs>

      {/* Edit Prompt Dialog */}
      {selectedPrompt && (
        <PromptEditor
          type={selectedPrompt.type}
          name={selectedPrompt.name}
          isOpen={isEditorOpen}
          onClose={() => {
            setIsEditorOpen(false);
            setSelectedPrompt(null);
          }}
          isNew={false}
        />
      )}

      {/* New Prompt Dialog */}
      <Dialog open={isNewPromptOpen} onOpenChange={setIsNewPromptOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New {newPromptType === 'role' ? 'Role' : 'Skill'}</DialogTitle>
            <DialogDescription>
              Enter a name for the new {newPromptType}. You'll be able to edit the content in the next step.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {newPromptType === 'role' ? 'Role' : 'Skill'} Name
              </label>
              <Input
                value={newPromptName}
                onChange={(e) => setNewPromptName(e.target.value)}
                placeholder={`Enter ${newPromptType} name...`}
                className="mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewPromptOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateNewPrompt} disabled={!newPromptName.trim()}>
              Create and Edit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}