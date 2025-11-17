import { CatppuccinThemeConfig } from '@/types/theme';

export const catppuccinThemes: CatppuccinThemeConfig[] = [
  {
    name: 'latte',
    displayName: 'Latte',
    isDark: false,
    colors: {
      // Primary Colors
      rosewater: '10 76.2% 95.1%',
      flamingo: '11 70% 93.5%',
      pink: '15 80% 91.4%',
      mauve: '16 78% 88.8%',
      red: '15 76% 69.4%',
      maroon: '14 72.4% 58.8%',
      peach: '20 84% 73.1%',
      yellow: '31 92% 76.5%',
      green: '21 80% 60.4%',
      teal: '28 68% 60.8%',
      sky: '33 78% 69%',
      sapphire: '29 68% 62.2%',
      blue: '35 78% 61.2%',
      lavender: '39 70% 73.5%',

      // Neutral Colors
      text: '11 15% 23.9%',
      subtext1: '11 8% 39.8%',
      subtext0: '11 6% 55.7%',
      overlay2: '11 4% 71.7%',
      overlay1: '11 3% 77.8%',
      overlay0: '11 2% 83.9%',
      surface2: '10 2% 90%',
      surface1: '10 1% 94%',
      surface0: '10 1% 96%',
      base: '10 13% 94.1%',
      mantle: '10 12% 92.5%',
      crust: '10 13% 90.8%',
    },
  },
  {
    name: 'frappe',
    displayName: 'Frappé',
    isDark: true,
    colors: {
      // Primary Colors
      rosewater: '13 28% 96.1%',
      flamingo: '13 40% 95.3%',
      pink: '16 67% 93.5%',
      mauve: '18 63% 91.8%',
      red: '13 64% 81.8%',
      maroon: '14 63% 72.4%',
      peach: '15 82% 86.7%',
      yellow: '27 87% 86.1%',
      green:  '21 71% 79.4%',
      teal:  '24 67% 79.6%',
      sky:   '22 78% 82.4%',
      sapphire: '22 82% 82.4%',
      blue:  '19 77% 82%',
      lavender: '18 65% 90%',

      // Neutral Colors
      text: '10 15% 89.8%',
      subtext1: '10 10% 76.5%',
      subtext0: '10 6% 63.3%',
      overlay2: '10 4% 50.2%',
      overlay1: '10 3% 43.9%',
      overlay0: '10 2% 37.6%',
      surface2: '10 2% 31.3%',
      surface1: '10 1% 25.1%',
      surface0: '10 1% 18.8%',
      base: '10 14% 15.1%',
      mantle: '10 12% 12.9%',
      crust: '10 13% 10.8%',
    },
  },
  {
    name: 'macchiato',
    displayName: 'Macchiato',
    isDark: true,
    colors: {
      // Primary Colors
      rosewater: '12 44% 96.3%',
      flamingo: '12 54% 95.5%',
      pink: '15 74% 94.1%',
      mauve: '16 68% 92.9%',
      red: '13 67% 84%',
      maroon: '14 65% 75.3%',
      peach: '15 84% 88.2%',
      yellow: '27 88% 87.8%',
      green: '21 73% 81%',
      teal: '23 70% 81.2%',
      sky: '24 79% 84%',
      sapphire: '24 83% 84%',
      blue: '21 80% 84.3%',
      lavender: '18 68% 91.2%',

      // Neutral Colors
      text: '10 16% 91.8%',
      subtext1: '10 11% 78%',
      subtext0: '10 7% 64.1%',
      overlay2: '10 4% 50.3%',
      overlay1: '10 3% 44.1%',
      overlay0: '10 2% 37.8%',
      surface2: '10 2% 31.5%',
      surface1: '10 1% 25.3%',
      surface0: '10 1% 19%',
      base: '10 16% 15.1%',
      mantle: '10 14% 12.9%',
      crust: '10 15% 11%',
    },
  },
  {
    name: 'mocha',
    displayName: 'Mocha',
    isDark: true,
    colors: {
      // Primary Colors
      rosewater: '10 57% 94.1%',
      flamingo: '10 71% 93.3%',
      pink: '15 80% 91.4%',
      mauve: '16 74% 90%',
      red: '11 72% 81.2%',
      maroon: '12 69% 71.6%',
      peach: '13 86% 87.1%',
      yellow: '23 89% 86.7%',
      green: '20 75% 82.7%',
      teal: '21 71% 82.9%',
      sky: '22 80% 85.7%',
      sapphire: '22 84% 85.7%',
      blue: '19 82% 85.3%',
      lavender: '18 70% 91%',

      // Neutral Colors
      text: '10 12% 95.1%',
      subtext1: '10 7% 80.5%',
      subtext0: '10 6% 65.7%',
      overlay2: '10 5% 50.8%',
      overlay1: '10 4% 44.5%',
      overlay0: '10 3% 38.3%',
      surface2: '10 2% 32%',
      surface1: '10 2% 25.8%',
      surface0: '10 2% 19.6%',
      base: '10 13% 15.1%',
      mantle: '10 12% 12.9%',
      crust: '10 14% 10.6%',
    },
  },
];

export const getThemeByName = (name: string): CatppuccinThemeConfig => {
  return catppuccinThemes.find(theme => theme.name === name) || catppuccinThemes[3]; // Default to mocha
};

export const getThemeBySystemPreference = (): CatppuccinTheme => {
  if (typeof window === 'undefined') return 'mocha';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'mocha' : 'latte';
};