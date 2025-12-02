import { FamilyRole, AdaptiveUILayout, QuickAction } from '../types/family';

export const getAdaptiveConfig = (role: FamilyRole): AdaptiveUILayout => {
  const baseConfig = {
    greeting: {
      morning: getGreetings(role, 'morning'),
      afternoon: getGreetings(role, 'afternoon'),
      evening: getGreetings(role, 'evening'),
    },
    quickActions: getQuickActions(role),
    layoutDensity: getLayoutDensity(role),
    fontSize: getFontSize(role),
    colorScheme: getColorScheme(role),
  };

  return baseConfig;
};

const getGreetings = (role: FamilyRole, timeOfDay: 'morning' | 'afternoon' | 'evening'): string[] => {
  const greetings = {
    parent: {
      morning: ['Good morning! Ready to tackle the day?', 'Morning! Let\'s check the family schedule'],
      afternoon: ['Hi! How\'s your day going?', 'Afternoon! Time to check on the kids'],
      evening: ['Evening! Let\'s wind down together', 'Good evening! Ready to relax?']
    },
    teenager: {
      morning: ['Morning! Got everything for school?', 'Hey! Ready for today?'],
      afternoon: ['What\'s up! How was school?', 'Hey! Homework time?'],
      evening: ['Yo! What\'s the plan tonight?', 'Hey! Need help with anything?']
    },
    child: {
      morning: ['Good morning! Ready for fun today?', 'Morning! Let\'s have a great day!'],
      afternoon: ['Hi! How was school? 😊', 'Hey! Ready to play?'],
      evening: ['Time to get ready for bed! 🌙', 'Evening! Story time?']
    },
    grandparent: {
      morning: ['Good morning! Hope you slept well', 'Morning! Ready for a peaceful day?'],
      afternoon: ['Good afternoon! Resting well?', 'Afternoon! Need anything?'],
      evening: ['Good evening! Time to relax', 'Evening! Comfortable and cozy?']
    }
  };

  return greetings[role][timeOfDay];
};

const getQuickActions = (role: FamilyRole): QuickAction[] => {
  const actions = {
    parent: [
      {
        id: 'family-status',
        label: 'Family Status',
        icon: 'users',
        action: () => console.log('Navigate to family status'),
        roles: ['parent'],
        priority: 1,
        category: 'family'
      },
      {
        id: 'schedule',
        label: 'Today\'s Schedule',
        icon: 'calendar',
        action: () => console.log('Navigate to schedule'),
        roles: ['parent'],
        priority: 2,
        category: 'schedule'
      },
      {
        id: 'reminders',
        label: 'Set Reminder',
        icon: 'bell',
        action: () => console.log('Open reminder creation'),
        roles: ['parent'],
        priority: 3,
        category: 'family'
      },
      {
        id: 'homework-help',
        label: 'Homework Help',
        icon: 'book-open',
        action: () => console.log('Navigate to homework help'),
        roles: ['parent'],
        priority: 4,
        category: 'homework'
      }
    ] as QuickAction[],
    teenager: [
      {
        id: 'homework',
        label: 'Homework Help',
        icon: 'book-open',
        action: () => console.log('Get homework help'),
        roles: ['teenager'],
        priority: 1,
        category: 'homework'
      },
      {
        id: 'schedule',
        label: 'My Schedule',
        icon: 'calendar',
        action: () => console.log('View my schedule'),
        roles: ['teenager'],
        priority: 2,
        category: 'schedule'
      },
      {
        id: 'friends',
        label: 'Connect with Friends',
        icon: 'message-circle',
        action: () => console.log('Open messaging'),
        roles: ['teenager'],
        priority: 3,
        category: 'social'
      },
      {
        id: 'music',
        label: 'Play Music',
        icon: 'music',
        action: () => console.log('Open music player'),
        roles: ['teenager'],
        priority: 4,
        category: 'entertainment'
      }
    ] as QuickAction[],
    child: [
      {
        id: 'games',
        label: 'Play Games 🎮',
        icon: 'gamepad-2',
        action: () => console.log('Open games'),
        roles: ['child'],
        priority: 1,
        category: 'entertainment'
      },
      {
        id: 'stories',
        label: 'Story Time 📚',
        icon: 'book',
        action: () => console.log('Listen to stories'),
        roles: ['child'],
        priority: 2,
        category: 'entertainment'
      },
      {
        id: 'homework',
        label: 'Homework Help ✏️',
        icon: 'pencil',
        action: () => console.log('Get homework help'),
        roles: ['child'],
        priority: 3,
        category: 'homework'
      },
      {
        id: 'videos',
        label: 'Watch Videos 📺',
        icon: 'play',
        action: () => console.log('Watch videos'),
        roles: ['child'],
        priority: 4,
        category: 'entertainment'
      }
    ] as QuickAction[],
    grandparent: [
      {
        id: 'family-updates',
        label: 'Family Updates',
        icon: 'users',
        action: () => console.log('View family updates'),
        roles: ['grandparent'],
        priority: 1,
        category: 'family'
      },
      {
        id: 'photos',
        label: 'Family Photos',
        icon: 'image',
        action: () => console.log('View photo gallery'),
        roles: ['grandparent'],
        priority: 2,
        category: 'family'
      },
      {
        id: 'calls',
        label: 'Video Call',
        icon: 'video',
        action: () => console.log('Start video call'),
        roles: ['grandparent'],
        priority: 3,
        category: 'family'
      },
      {
        id: 'reminders',
        label: 'My Reminders',
        icon: 'bell',
        action: () => console.log('View reminders'),
        roles: ['grandparent'],
        priority: 4,
        category: 'family'
      }
    ] as QuickAction[]
  };

  return actions[role];
};

const getLayoutDensity = (role: FamilyRole): 'spacious' | 'comfortable' | 'compact' => {
  switch (role) {
    case 'child':
    case 'grandparent':
      return 'spacious'; // Larger touch targets, more spacing
    case 'parent':
      return 'comfortable'; // Balanced density
    case 'teenager':
      return 'compact'; // More information dense
  }
};

const getFontSize = (role: FamilyRole): 'small' | 'medium' | 'large' | 'extra-large' => {
  switch (role) {
    case 'grandparent':
      return 'extra-large'; // Very large text for readability
    case 'child':
      return 'large'; // Large text for developing readers
    case 'parent':
      return 'medium'; // Standard adult size
    case 'teenager':
      return 'small'; // Compact for teens
  }
};

const getColorScheme = (role: FamilyRole): 'playful' | 'calm' | 'professional' | 'accessible' => {
  switch (role) {
    case 'child':
      return 'playful'; // Bright, engaging colors
    case 'grandparent':
      return 'accessible'; // High contrast, clear
    case 'parent':
      return 'professional'; // Balanced, sophisticated
    case 'teenager':
      return 'calm'; // Modern, muted tones
  }
};

export const getTimeOfDay = (): 'morning' | 'afternoon' | 'evening' => {
  const hour = new Date().getHours();
  if (hour < 12) return 'morning';
  if (hour < 18) return 'afternoon';
  return 'evening';
};