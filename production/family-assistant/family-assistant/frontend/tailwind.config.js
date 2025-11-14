/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    {
      pattern: /^(bg|text|border)-(ctp)-.+$/,
    },
  ],
  theme: {
    extend: {
      colors: {
        // Catppuccin colors via CSS variables
        ctp: {
          base: 'rgb(var(--ctp-base) / <alpha-value>)',
          mantle: 'rgb(var(--ctp-mantle) / <alpha-value>)',
          crust: 'rgb(var(--ctp-crust) / <alpha-value>)',
          surface0: 'rgb(var(--ctp-surface0) / <alpha-value>)',
          surface1: 'rgb(var(--ctp-surface1) / <alpha-value>)',
          surface2: 'rgb(var(--ctp-surface2) / <alpha-value>)',
          overlay0: 'rgb(var(--ctp-overlay0) / <alpha-value>)',
          overlay1: 'rgb(var(--ctp-overlay1) / <alpha-value>)',
          overlay2: 'rgb(var(--ctp-overlay2) / <alpha-value>)',
          subtext0: 'rgb(var(--ctp-subtext0) / <alpha-value>)',
          subtext1: 'rgb(var(--ctp-subtext1) / <alpha-value>)',
          text: 'rgb(var(--ctp-text) / <alpha-value>)',
          rosewater: 'rgb(var(--ctp-rosewater) / <alpha-value>)',
          flamingo: 'rgb(var(--ctp-flamingo) / <alpha-value>)',
          pink: 'rgb(var(--ctp-pink) / <alpha-value>)',
          mauve: 'rgb(var(--ctp-mauve) / <alpha-value>)',
          red: 'rgb(var(--ctp-red) / <alpha-value>)',
          maroon: 'rgb(var(--ctp-maroon) / <alpha-value>)',
          peach: 'rgb(var(--ctp-peach) / <alpha-value>)',
          yellow: 'rgb(var(--ctp-yellow) / <alpha-value>)',
          green: 'rgb(var(--ctp-green) / <alpha-value>)',
          teal: 'rgb(var(--ctp-teal) / <alpha-value>)',
          sky: 'rgb(var(--ctp-sky) / <alpha-value>)',
          sapphire: 'rgb(var(--ctp-sapphire) / <alpha-value>)',
          blue: 'rgb(var(--ctp-blue) / <alpha-value>)',
          lavender: 'rgb(var(--ctp-lavender) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}