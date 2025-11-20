export type FamilyRole = 'parent' | 'teenager' | 'child' | 'grandparent';

export interface FamilyMember {
  id: string;
  name: string;
  role: FamilyRole;
  avatar?: string;
  age: number;
  isOnline: boolean;
  currentActivity?: string;
  location?: {
    name: string;
    lat: number;
    lng: number;
  };
  preferences: {
    language: 'en' | 'es';
    voiceGender: 'male' | 'female' | 'neutral';
    theme: 'light' | 'dark' | 'auto';
    textSize: 'small' | 'medium' | 'large' | 'extra-large';
  };
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  action: () => void;
  roles: FamilyRole[];
  priority: number;
  category: 'homework' | 'schedule' | 'family' | 'entertainment' | 'safety';
}

export interface FamilyActivity {
  id: string;
  memberId: string;
  type: 'homework' | 'chore' | 'entertainment' | 'social' | 'school' | 'sleep' | 'family';
  title: string;
  description?: string;
  startTime: Date;
  endTime?: Date;
  status: 'active' | 'completed' | 'paused';
}

export interface VoiceCommand {
  id: string;
  transcript: string;
  confidence: number;
  timestamp: Date;
  memberId: string;
  response?: string;
  category: 'question' | 'command' | 'reminder' | 'homework' | 'entertainment';
}

export interface Reminder {
  id: string;
  title: string;
  description?: string;
  forMembers: string[];
  createdBy: string;
  scheduledTime: Date;
  isRecurring: boolean;
  category: 'homework' | 'chore' | 'appointment' | 'medication' | 'activity';
  status: 'pending' | 'completed' | 'dismissed';
}

export interface ConversationMessage {
  id: string;
  content: string;
  type: 'text' | 'voice' | 'image' | 'document';
  sender: 'user' | 'assistant';
  memberId: string;
  timestamp: Date;
  metadata?: {
    duration?: number; // for voice messages
    imageUrl?: string;
    fileName?: string;
  };
}

export interface AdaptiveUILayout {
  greeting: {
    morning: string[];
    afternoon: string[];
    evening: string[];
  };
  quickActions: QuickAction[];
  layoutDensity: 'spacious' | 'comfortable' | 'compact';
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  colorScheme: 'playful' | 'calm' | 'professional' | 'accessible';
}