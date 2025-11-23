"use client";

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useRoles, useSkills, useTestPromptAssembly } from '@/hooks/useKnowledge';
import { PromptAssemblyTest } from '@/types/knowledge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, Play, Eye, BarChart3, Zap } from 'lucide-react';

const MOCK_USERS = [
  { id: 'user-123', name: 'John (Parent)' },
  { id: 'user-456', name: 'Sarah (Child)' },
  { id: 'user-789', name: 'Mike (Teenager)' },
];

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'bilingual', label: 'Bilingual' },
];

export default function PromptTester() {
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [showPrompt, setShowPrompt] = useState(false);

  const { data: roles, isLoading: rolesLoading } = useRoles();
  const { data: skills, isLoading: skillsLoading } = useSkills();
  const testPromptAssembly = useTestPromptAssembly();

  const handleTest = async () => {
    if (!selectedUser || !selectedRole) return;

    testPromptAssembly.mutate({
      userId: selectedUser,
      role: selectedRole,
      language: selectedLanguage,
    });
  };

  const isLoading = rolesLoading || skillsLoading || testPromptAssembly.isPending;
  const testResult = testPromptAssembly.data;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Prompt Assembly Tester</span>
        </CardTitle>
        <CardDescription>
          Test how roles, skills, and language preferences combine to create the final AI prompt.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {testPromptAssembly.error && (
          <Alert variant="destructive">
            <AlertDescription>
              Test failed: {(testPromptAssembly.error as Error).message}
            </AlertDescription>
          </Alert>
        )}

        {/* Test Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* User Selection */}
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Test User
            </label>
            <Select value={selectedUser} onValueChange={setSelectedUser} disabled={isLoading}>
              <SelectTrigger>
                <SelectValue placeholder="Select user..." />
              </SelectTrigger>
              <SelectContent>
                {MOCK_USERS.map((user) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Role Selection */}
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Role
            </label>
            <Select value={selectedRole} onValueChange={setSelectedRole} disabled={isLoading}>
              <SelectTrigger>
                <SelectValue placeholder="Select role..." />
              </SelectTrigger>
              <SelectContent>
                {roles?.map((role) => (
                  <SelectItem key={role} value={role}>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">{role}</Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Language Selection */}
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Language
            </label>
            <Select value={selectedLanguage} onValueChange={setSelectedLanguage} disabled={isLoading}>
              <SelectTrigger>
                <SelectValue placeholder="Select language..." />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Test Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleTest}
            disabled={isLoading || !selectedUser || !selectedRole}
            size="lg"
          >
            {testPromptAssembly.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Test Prompt Assembly
          </Button>
        </div>

        {/* Test Results */}
        {testResult && (
          <div className="space-y-4">
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium mb-3">Test Results</h3>

              {/* Token Reduction Stats */}
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg mb-4">
                <h4 className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
                  Token Reduction Stats
                </h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Original:</span>
                    <span className="ml-2 font-mono">{testResult.token_reduction.original}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Compressed:</span>
                    <span className="ml-2 font-mono">{testResult.token_reduction.compressed}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Savings:</span>
                    <span className="ml-2 font-mono text-green-600 dark:text-green-400">
                      {testResult.token_reduction.savings_percent}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Prompt Preview Toggle */}
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium">Assembled Prompt</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPrompt(!showPrompt)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  {showPrompt ? 'Hide' : 'Show'} Prompt
                </Button>
              </div>

              {/* Prompt Content */}
              {showPrompt && (
                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <div className="max-h-96 overflow-y-auto">
                    <pre className="text-xs font-mono whitespace-pre-wrap">
                      {testResult.full_prompt}
                    </pre>
                  </div>
                  <div className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                    Length: {testResult.full_prompt.length} characters
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Available Skills Info */}
        {skills && skills.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2 flex items-center">
              <Zap className="h-4 w-4 mr-2" />
              Available Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-2">
              These skills may be included in the prompt based on the user's active skills configuration.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}