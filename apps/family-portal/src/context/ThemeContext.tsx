import React, { createContext, useContext, useEffect, useState } from 'react';
import { FamilyMember } from '../types/family';

type ThemeMode = 'light' | 'dark' | 'auto';

interface ThemeContextType {
  theme: ThemeMode;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: ThemeMode) => void;
  systemPreference: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
  currentUser?: FamilyMember;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children, currentUser }) => {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    // Load from localStorage or default to user preference
    const saved = localStorage.getItem('family-assistant-theme') as ThemeMode;
    if (saved && ['light', 'dark', 'auto'].includes(saved)) {
      return saved;
    }
    return currentUser?.preferences.theme === 'auto' ? 'auto' :
           currentUser?.preferences.theme === 'dark' ? 'dark' : 'light';
  });

  const [systemPreference, setSystemPreference] = useState<'light' | 'dark'>('light');

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      setSystemPreference(e.matches ? 'dark' : 'light');
    };

    // Set initial value
    setSystemPreference(mediaQuery.matches ? 'dark' : 'light');

    // Listen for changes
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Apply theme to document
  useEffect(() => {
    const isDark = theme === 'dark' || (theme === 'auto' && systemPreference === 'dark');

    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Save to localStorage
    localStorage.setItem('family-assistant-theme', theme);
  }, [theme, systemPreference]);

  const isDark = theme === 'dark' || (theme === 'auto' && systemPreference === 'dark');

  const toggleTheme = () => {
    setThemeState(current => {
      switch (current) {
        case 'light': return 'dark';
        case 'dark': return 'auto';
        case 'auto': return 'light';
        default: return 'light';
      }
    });
  };

  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
  };

  const value: ThemeContextType = {
    theme,
    isDark,
    toggleTheme,
    setTheme,
    systemPreference,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};