"use client";

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { UserProfile } from '@/types/knowledge';
import { useUserProfile, useUpdateUserProfile, useRoles, useSkills } from '@/hooks/useKnowledge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, Save, Users, Zap } from 'lucide-react';

interface UserSkillAssignerProps {
  userId: string;
  userName?: string;
}

const ROLES = ['parent', 'child', 'teenager', 'grandparent', 'guardian'];
const AGE_GROUPS = ['toddler', 'child', 'pre-teen', 'teenager', 'young-adult', 'adult', 'senior'];
const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'bilingual', label: 'Bilingual (English/Spanish)' },
];

export default function UserSkillAssigner({ userId, userName }: UserSkillAssignerProps) {
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedAgeGroup, setSelectedAgeGroup] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState<'en' | 'es' | 'bilingual'>('en');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  const { data: userProfile, isLoading: profileLoading, error: profileError } = useUserProfile(userId);
  const { data: availableRoles, isLoading: rolesLoading } = useRoles();
  const { data: availableSkills, isLoading: skillsLoading } = useSkills();

  const updateUserProfile = useUpdateUserProfile();

  // Initialize form with user's current profile
  if (userProfile && !selectedRole) {
    setSelectedRole(userProfile.role);
    setSelectedAgeGroup(userProfile.age_group || '');
    setSelectedLanguage(userProfile.language_preference);
    setSelectedSkills(userProfile.active_skills || []);
  }

  const handleSkillToggle = (skill: string, checked: boolean) => {
    if (checked) {
      setSelectedSkills(prev => [...prev, skill]);
    } else {
      setSelectedSkills(prev => prev.filter(s => s !== skill));
    }
  };

  const handleSave = async () => {
    const updateData: Partial<UserProfile> = {
      role: selectedRole,
      age_group: selectedAgeGroup || undefined,
      language_preference: selectedLanguage,
      active_skills: selectedSkills,
    };

    updateUserProfile.mutate({
      userId,
      data: updateData,
    });
  };

  const isLoading = profileLoading || rolesLoading || skillsLoading || updateUserProfile.isPending;

  if (profileError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load user profile: {(profileError as Error).message}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Users className="h-5 w-5" />
          <span>Knowledge Configuration for {userName || userId}</span>
        </CardTitle>
        <CardDescription>
          Configure the user's role, language preference, and active skills for AI interactions.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {updateUserProfile.error && (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to update profile: {(updateUserProfile.error as Error).message}
            </AlertDescription>
          </Alert>
        )}

        {updateUserProfile.isSuccess && (
          <Alert>
            <AlertDescription>
              Profile updated successfully!
            </AlertDescription>
          </Alert>
        )}

        {/* Role Selection */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
            User Role
          </label>
          <Select value={selectedRole} onValueChange={setSelectedRole} disabled={isLoading}>
            <SelectTrigger>
              <SelectValue placeholder="Select a role..." />
            </SelectTrigger>
            <SelectContent>
              {[...ROLES, ...(availableRoles || [])].map((role) => (
                <SelectItem key={role} value={role}>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">{role}</Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Defines how the user interacts with the AI assistant
          </p>
        </div>

        {/* Age Group Selection */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
            Age Group (Optional)
          </label>
          <Select value={selectedAgeGroup} onValueChange={setSelectedAgeGroup} disabled={isLoading}>
            <SelectTrigger>
              <SelectValue placeholder="Select age group..." />
            </SelectTrigger>
            <SelectContent>
              {AGE_GROUPS.map((ageGroup) => (
                <SelectItem key={ageGroup} value={ageGroup}>
                  {ageGroup}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Helps tailor responses to be age-appropriate
          </p>
        </div>

        {/* Language Preference */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
            Language Preference
          </label>
          <Select value={selectedLanguage} onValueChange={(value) => setSelectedLanguage(value as 'en' | 'es' | 'bilingual')} disabled={isLoading}>
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
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Preferred language for AI responses
          </p>
        </div>

        {/* Skills Selection */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 block">
            Active Skills
          </label>
          {skillsLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading skills...</span>
            </div>
          ) : availableSkills && availableSkills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableSkills.map((skill) => (
                <div key={skill} className="flex items-center space-x-2 p-3 border rounded-lg">
                  <Checkbox
                    id={`skill-${skill}`}
                    checked={selectedSkills.includes(skill)}
                    onCheckedChange={(checked) => handleSkillToggle(skill, checked as boolean)}
                    disabled={isLoading}
                  />
                  <div className="flex items-center space-x-2 flex-1">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    <label
                      htmlFor={`skill-${skill}`}
                      className="text-sm font-medium cursor-pointer flex-1"
                    >
                      {skill}
                    </label>
                    <Badge variant="secondary" className="text-xs">
                      skill
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400 border rounded-lg">
              No skills available. Create skills in the Knowledge Base first.
            </div>
          )}
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
            Select the skills this user can access for specialized assistance
          </p>
        </div>

        {/* Current Selection Summary */}
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Current Selection</h4>
          <div className="flex flex-wrap gap-2">
            {selectedRole && (
              <Badge variant="default">
                Role: {selectedRole}
              </Badge>
            )}
            {selectedAgeGroup && (
              <Badge variant="outline">
                Age: {selectedAgeGroup}
              </Badge>
            )}
            <Badge variant="outline">
              Lang: {LANGUAGES.find(l => l.value === selectedLanguage)?.label}
            </Badge>
            {selectedSkills.length > 0 && (
              <Badge variant="secondary">
                Skills: {selectedSkills.length}
              </Badge>
            )}
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isLoading || !selectedRole}>
            {updateUserProfile.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save Configuration
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}