export type CatppuccinTheme = 'latte' | 'frappe' | 'macchiato' | 'mocha';

export interface CatppuccinColors {
  // Primary Colors
  rosewater: string;
  flamingo: string;
  pink: string;
  mauve: string;
  red: string;
  maroon: string;
  peach: string;
  yellow: string;
  green: string;
  teal: string;
  sky: string;
  sapphire: string;
  blue: string;
  lavender: string;

  // Neutral Colors
  text: string;
  subtext1: string;
  subtext0: string;
  overlay2: string;
  overlay1: string;
  overlay0: string;
  surface2: string;
  surface1: string;
  surface0: string;
  base: string;
  mantle: string;
  crust: string;
}

export interface CatppuccinThemeConfig {
  name: CatppuccinTheme;
  displayName: string;
  colors: CatppuccinColors;
  isDark: boolean;
}

export interface ThemeContextType {
  theme: CatppuccinTheme;
  setTheme: (theme: CatppuccinTheme) => void;
  resolvedTheme: CatppuccinTheme;
  themes: CatppuccinThemeConfig[];
  isSystem: boolean;
  setSystem: (isSystem: boolean) => void;
}