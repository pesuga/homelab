"use client";

import { useState, useEffect } from 'react';
import { useCorePrompts, useSkills, useCorePromptDetail, useUpdateCorePrompt } from '@/hooks/useKnowledge';
import PromptEditor from '@/components/knowledge/PromptEditor';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Loader2, Plus, Edit, FileText, Zap, Save, X, History } from 'lucide-react';
import { CorePromptMetadata } from '@/types/knowledge';

export default function KnowledgePage() {
  const [selectedPrompt, setSelectedPrompt] = useState<{ type: 'core' | 'skill'; name: string } | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isCoreEditorOpen, setIsCoreEditorOpen] = useState(false);
  const [isNewSkillOpen, setIsNewSkillOpen] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [editingCorePrompt, setEditingCorePrompt] = useState<string | null>(null);
  const [corePromptContent, setCorePromptContent] = useState('');
  const [changeDescription, setChangeDescription] = useState('');

  const { data: corePromptsData, isLoading: coreLoading, error: coreError } = useCorePrompts();
  const { data: skills, isLoading: skillsLoading, error: skillsError } = useSkills();
  const { data: corePromptDetail, isLoading: detailLoading } = useCorePromptDetail(editingCorePrompt || '');
  const updateCorePrompt = useUpdateCorePrompt();

  const corePrompts = corePromptsData?.prompts || [];

  const handleEditCorePrompt = (name: string) => {
    setEditingCorePrompt(name);
    setIsCoreEditorOpen(true);
    setChangeDescription('');
  };

  const handleSaveCorePrompt = async () => {
    if (!editingCorePrompt || !corePromptContent) return;

    try {
      await updateCorePrompt.mutateAsync({
        name: editingCorePrompt,
        content: corePromptContent,
        changeSummary: changeDescription || undefined,
      });
      setIsCoreEditorOpen(false);
      setEditingCorePrompt(null);
      setCorePromptContent('');
      setChangeDescription('');
    } catch (error) {
      console.error('Failed to save core prompt:', error);
    }
  };

  const handleEditSkill = (name: string) => {
    setSelectedPrompt({ type: 'skill', name });
    setIsEditorOpen(true);
  };

  const handleNewSkill = () => {
    setNewSkillName('');
    setIsNewSkillOpen(true);
  };

  const handleCreateNewSkill = () => {
    if (!newSkillName.trim()) return;

    setIsNewSkillOpen(false);
    setSelectedPrompt({ type: 'skill', name: newSkillName.trim() });
    setIsEditorOpen(true);
  };

  // Update content when detail loads
  useEffect(() => {
    if (corePromptDetail && editingCorePrompt && !corePromptContent) {
      setCorePromptContent(corePromptDetail.content);
    }
  }, [corePromptDetail, editingCorePrompt, corePromptContent]);

  const CorePromptsList = () => {
    if (coreError) {
      return (
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load core prompts: {coreError.message}
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <CardTitle>Core System Prompts</CardTitle>
          </div>
          <CardDescription>
            Foundation prompts that define the AI assistant's behavior and capabilities.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {coreLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2 text-gray-700 dark:text-gray-300">Loading core prompts...</span>
            </div>
          ) : corePrompts.length > 0 ? (
            <div className="grid gap-3">
              {corePrompts.map((prompt: CorePromptMetadata) => (
                <div
                  key={prompt.name}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Badge variant="default">CORE</Badge>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">{prompt.display_name || prompt.name}</span>
                      {prompt.version_count > 0 && (
                        <Badge variant="outline">{prompt.version_count} {prompt.version_count === 1 ? 'version' : 'versions'}</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {prompt.last_modified ? `Last updated: ${new Date(prompt.last_modified).toLocaleString()}` : 'No versions yet'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditCorePrompt(prompt.name)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No core prompts found.
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const SkillsList = () => {
    if (skillsError) {
      return (
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load skills: {skillsError.message}
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <CardTitle>Skills</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewSkill}
              disabled={skillsLoading}
            >
              <Plus className="h-4 w-4 mr-2" />
              New Skill
            </Button>
          </div>
          <CardDescription>
            Specialized capabilities like calendar assistant, coding tutor, etc.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {skillsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2 text-gray-700 dark:text-gray-300">Loading skills...</span>
            </div>
          ) : skills && skills.length > 0 ? (
            <div className="grid gap-3">
              {skills.map((skill) => (
                <div
                  key={skill}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <Badge variant="secondary">SKILL</Badge>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{skill}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditSkill(skill)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No skills found. Create your first skill to get started.
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Knowledge Base</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage core prompts and skills that define the AI assistant's capabilities.
        </p>
      </div>

      <Tabs defaultValue="core" className="space-y-6">
        <TabsList>
          <TabsTrigger value="core">Core Prompts</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
        </TabsList>

        <TabsContent value="core">
          <CorePromptsList />
        </TabsContent>

        <TabsContent value="skills">
          <SkillsList />
        </TabsContent>
      </Tabs>

      {/* Core Prompt Editor Dialog */}
      <Dialog open={isCoreEditorOpen} onOpenChange={setIsCoreEditorOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Edit Core Prompt: {editingCorePrompt}</span>
            </DialogTitle>
            <DialogDescription>
              Modify the core system prompt. Version history will be maintained automatically.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 overflow-y-auto">
            {detailLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading prompt...</span>
              </div>
            ) : (
              <>
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Change Description (Optional)
                  </label>
                  <Input
                    value={changeDescription}
                    onChange={(e) => setChangeDescription(e.target.value)}
                    placeholder="Describe what you changed..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Prompt Content
                  </label>
                  <Textarea
                    value={corePromptContent}
                    onChange={(e) => setCorePromptContent(e.target.value)}
                    className="mt-1 min-h-[400px] font-mono text-sm"
                    placeholder="Enter prompt content..."
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCoreEditorOpen(false);
                setEditingCorePrompt(null);
                setCorePromptContent('');
                setChangeDescription('');
              }}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button
              onClick={handleSaveCorePrompt}
              disabled={!corePromptContent || updateCorePrompt.isPending}
            >
              {updateCorePrompt.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Version
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Skill Editor Dialog */}
      {selectedPrompt && selectedPrompt.type === 'skill' && (
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

      {/* New Skill Dialog */}
      <Dialog open={isNewSkillOpen} onOpenChange={setIsNewSkillOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Skill</DialogTitle>
            <DialogDescription>
              Enter a name for the new skill. You'll be able to edit the content in the next step.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Skill Name
              </label>
              <Input
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="Enter skill name..."
                className="mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewSkillOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateNewSkill} disabled={!newSkillName.trim()}>
              Create and Edit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
