"use client";

import { useState, useEffect } from 'react';
import { useUserProfile, useUpdateUserProfile, useRoles, useSkills } from '@/hooks/useKnowledge';
import { UserProfile } from '@/types/knowledge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Save, X, TestTube } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface UserProfileEditorProps {
  userId: string;
  userName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function UserProfileEditor({
  userId,
  userName,
  isOpen,
  onClose,
  onSuccess
}: UserProfileEditorProps) {
  const { data: profile, isLoading, error } = useUserProfile(userId);
  const updateProfile = useUpdateUserProfile();
  const { data: roles } = useRoles();
  const { data: skills } = useSkills();

  const [formData, setFormData] = useState<Partial<UserProfile>>({
    role: '',
    age_group: '',
    language_preference: 'en',
    active_skills: [],
    preferences: {}
  });

  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  useEffect(() => {
    if (profile) {
      setFormData({
        role: profile.role,
        age_group: profile.age_group || '',
        language_preference: profile.language_preference,
        active_skills: profile.active_skills || [],
        preferences: profile.preferences || {}
      });
      setSelectedSkills(profile.active_skills || []);
    }
  }, [profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateProfile.mutateAsync({
        userId,
        data: {
          ...formData,
          active_skills: selectedSkills
        }
      });
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative z-50 w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Edit Profile: {userName}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Configure AI assistant settings and preferences
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            Loading profile...
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to load profile: {error.message}
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Role Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Role</CardTitle>
                <CardDescription>
                  Define the user's primary role in the family
                </CardDescription>
              </CardHeader>
              <CardContent>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  required
                >
                  <option value="">Select a role...</option>
                  {roles?.map((role) => (
                    <option key={role} value={role}>
                      {role.charAt(0).toUpperCase() + role.slice(1)}
                    </option>
                  ))}
                </select>
              </CardContent>
            </Card>

            {/* Age Group */}
            <Card>
              <CardHeader>
                <CardTitle>Age Group</CardTitle>
                <CardDescription>
                  Helps tailor responses appropriately
                </CardDescription>
              </CardHeader>
              <CardContent>
                <select
                  value={formData.age_group}
                  onChange={(e) => setFormData(prev => ({ ...prev, age_group: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Select age group...</option>
                  <option value="child">Child (6-12)</option>
                  <option value="teenager">Teenager (13-17)</option>
                  <option value="adult">Adult (18-64)</option>
                  <option value="senior">Senior (65+)</option>
                </select>
              </CardContent>
            </Card>

            {/* Language Preference */}
            <Card>
              <CardHeader>
                <CardTitle>Language Preference</CardTitle>
                <CardDescription>
                  Preferred language for AI interactions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <select
                  value={formData.language_preference}
                  onChange={(e) => setFormData(prev => ({ ...prev, language_preference: e.target.value as 'en' | 'es' | 'bilingual' }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="bilingual">Bilingual</option>
                </select>
              </CardContent>
            </Card>

            {/* Active Skills */}
            <Card>
              <CardHeader>
                <CardTitle>Active Skills</CardTitle>
                <CardDescription>
                  Select specialized AI skills that are enabled for this user
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {skills?.map((skill) => (
                    <button
                      key={skill}
                      type="button"
                      onClick={() => toggleSkill(skill)}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        selectedSkills.includes(skill)
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      <div className="flex flex-col items-center">
                        <Zap className="h-5 w-5 mb-1" />
                        <span className="text-sm font-medium">{skill}</span>
                      </div>
                    </button>
                  ))}
                </div>
                {selectedSkills.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Selected skills:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedSkills.map((skill) => (
                        <Badge key={skill} variant="secondary">
                          {skill}
                          <button
                            type="button"
                            onClick={() => toggleSkill(skill)}
                            className="ml-1 hover:text-red-500"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Form Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={updateProfile.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateProfile.isPending}
              >
                {updateProfile.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Profile
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

const Zap = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);