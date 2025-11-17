"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { CatppuccinTheme, ThemeContextType } from '@/types/theme';
import { catppuccinThemes, getThemeBySystemPreference, getThemeByName } from '@/data/catppuccin-colors';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'catppuccin-theme';
const SYSTEM_KEY = 'catppuccin-theme-system';

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: CatppuccinTheme;
}

export function ThemeProvider({ children, defaultTheme = 'mocha' }: ThemeProviderProps) {
  const [theme, setTheme] = useState<CatppuccinTheme>('mocha');
  const [isSystem, setIsSystem] = useState<boolean>(false);
  const [resolvedTheme, setResolvedTheme] = useState<CatppuccinTheme>('mocha');
  const [mounted, setMounted] = useState(false);

  // Load theme from localStorage on mount
  useEffect(() => {
    setMounted(true);

    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem(STORAGE_KEY) as CatppuccinTheme;
      const savedSystem = localStorage.getItem(SYSTEM_KEY) === 'true';

      if (savedSystem) {
        setIsSystem(true);
        const systemTheme = getThemeBySystemPreference();
        setTheme(systemTheme);
        setResolvedTheme(systemTheme);
      } else if (savedTheme && catppuccinThemes.find(t => t.name === savedTheme)) {
        setTheme(savedTheme);
        setResolvedTheme(savedTheme);
      } else {
        setResolvedTheme(defaultTheme);
      }
    }
  }, [defaultTheme]);

  // Apply theme to document element
  useEffect(() => {
    if (!mounted || typeof window === 'undefined') return;

    const root = document.documentElement;

    // Remove all existing theme classes
    root.classList.remove('theme-latte', 'theme-frappe', 'theme-macchiato', 'theme-mocha');

    // Add current theme class
    root.classList.add(`theme-${theme}`);
    root.setAttribute('data-theme', theme);

    // Apply CSS custom properties
    const themeConfig = getThemeByName(theme);
    Object.entries(themeConfig.colors).forEach(([key, value]) => {
      root.style.setProperty(`--catppuccin-${key}`, value);
    });

  }, [theme, mounted]);

  // Handle system preference changes
  useEffect(() => {
    if (!mounted || typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      if (isSystem) {
        const systemTheme = getThemeBySystemPreference();
        setTheme(systemTheme);
        setResolvedTheme(systemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [isSystem, mounted]);

  const handleSetTheme = (newTheme: CatppuccinTheme) => {
    setTheme(newTheme);
    setResolvedTheme(newTheme);
    setIsSystem(false);

    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, newTheme);
      localStorage.setItem(SYSTEM_KEY, 'false');
    }
  };

  const handleSetSystem = (useSystem: boolean) => {
    setIsSystem(useSystem);

    if (typeof window !== 'undefined') {
      localStorage.setItem(SYSTEM_KEY, useSystem.toString());

      if (useSystem) {
        const systemTheme = getThemeBySystemPreference();
        setTheme(systemTheme);
        setResolvedTheme(systemTheme);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  };

  
  const value: ThemeContextType = {
    theme,
    setTheme: handleSetTheme,
    resolvedTheme,
    themes: catppuccinThemes,
    isSystem,
    setSystem: handleSetSystem,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}