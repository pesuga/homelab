import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeService } from '@/services/knowledgeService';
import { Prompt, UserProfile, PromptAssemblyTest } from '@/types/knowledge';

export const useRoles = () => {
  return useQuery({
    queryKey: ['roles'],
    queryFn: knowledgeService.getRoles,
  });
};

export const useSkills = () => {
  return useQuery({
    queryKey: ['skills'],
    queryFn: knowledgeService.getSkills,
  });
};

export const useRolePrompt = (role: string) => {
  return useQuery({
    queryKey: ['role', role],
    queryFn: () => knowledgeService.getRolePrompt(role),
    enabled: !!role,
  });
};

export const useSkillPrompt = (skill: string) => {
  return useQuery({
    queryKey: ['skill', skill],
    queryFn: () => knowledgeService.getSkillPrompt(skill),
    enabled: !!skill,
  });
};

export const useSaveRolePrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ role, content }: { role: string; content: string }) =>
      knowledgeService.saveRolePrompt(role, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      queryClient.invalidateQueries({ queryKey: ['role'] });
    },
  });
};

export const useSaveSkillPrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ skill, content }: { skill: string; content: string }) =>
      knowledgeService.saveSkillPrompt(skill, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['skill'] });
    },
  });
};

export const useDeleteRolePrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ role }: { role: string }) =>
      knowledgeService.deleteRolePrompt(role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      queryClient.invalidateQueries({ queryKey: ['role'] });
    },
  });
};

export const useDeleteSkillPrompt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ skill }: { skill: string }) =>
      knowledgeService.deleteSkillPrompt(skill),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['skill'] });
    },
  });
};

export const useUserProfile = (userId: string) => {
  return useQuery({
    queryKey: ['user-profile', userId],
    queryFn: () => knowledgeService.getUserProfile(userId),
    enabled: !!userId
  });
};

export const useUpdateUserProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: Partial<any> }) =>
      knowledgeService.updateUserProfile(userId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['user-profile', variables.userId] });
    }
  });
};

export const useTestPromptAssembly = () => {
  return useMutation({
    mutationFn: ({ userId, role, language }: { userId: string; role: string; language: string }) =>
      knowledgeService.testPromptAssembly(userId, role, language),
  });
};