import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { catppuccin, CatppuccinFlavor, defaultFlavor } from '../styles/themes/catppuccin';

interface ThemeContextType {
  flavor: CatppuccinFlavor;
  setFlavor: (flavor: CatppuccinFlavor) => void;
  colors: typeof catppuccin[CatppuccinFlavor]['colors'];
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'catppuccin-flavor';

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [flavor, setFlavorState] = useState<CatppuccinFlavor>(() => {
    // Load from localStorage or use default
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    return (saved as CatppuccinFlavor) || defaultFlavor;
  });

  const setFlavor = (newFlavor: CatppuccinFlavor) => {
    setFlavorState(newFlavor);
    localStorage.setItem(THEME_STORAGE_KEY, newFlavor);
  };

  const theme = catppuccin[flavor];

  // Helper to convert hex to RGB
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `${parseInt(result[1], 16)} ${parseInt(result[2], 16)} ${parseInt(result[3], 16)}`
      : '0 0 0';
  };

  // Apply CSS variables to :root
  useEffect(() => {
    const root = document.documentElement;
    const colors = theme.colors;

    // Apply all Catppuccin colors as CSS variables (in RGB format for Tailwind opacity)
    Object.entries(colors).forEach(([name, value]) => {
      root.style.setProperty(`--ctp-${name}`, hexToRgb(value));
    });

    // Set data attribute for theme-based styling
    root.setAttribute('data-theme', flavor);
    root.setAttribute('data-theme-dark', theme.dark.toString());
  }, [flavor, theme]);

  return (
    <ThemeContext.Provider
      value={{
        flavor,
        setFlavor,
        colors: theme.colors,
        isDark: theme.dark,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
