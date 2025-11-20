/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Warm, family-friendly color palette
        primary: {
          50: '#fef7f0',
          100: '#fdead2',
          200: '#fad9a5',
          300: '#f7c271',
          400: '#f4a643',
          500: '#f29224', // Primary orange
          600: '#e67e14',
          700: '#c86a0f',
          800: '#a6561a',
          900: '#884820',
        },
        // Role-specific accent colors
        accent: {
          parent: '#9b59b6', // Purple - wisdom, authority
          teen: '#3498db',   // Blue - energy, modern
          child: '#f1c40f',  // Yellow - fun, creativity
          grandparent: '#16a085', // Teal - calm, stability
        },
        // Calm backgrounds
        neutral: {
          50: '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#d6d3d1',
          400: '#a8a29e',
          500: '#78716c',
          600: '#57534e',
          700: '#44403c',
          800: '#292524',
          900: '#1c1917',
        },
        // Status colors
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6',
        // Dark mode specific colors
        dark: {
          bg: {
            primary: '#0f0f0f',      // Deep black for main background
            secondary: '#1a1a1a',    // Slightly lighter for cards
            tertiary: '#262626',     // For hover states
            card: '#1a1a1a',         // Card backgrounds
            elevated: '#262626',     // Elevated surfaces
          },
          text: {
            primary: '#ffffff',      // Main text
            secondary: '#d4d4d8',    // Secondary text
            muted: '#71717a',        // Muted text
            accent: '#fbbf24',       // Accent text
          },
          border: {
            primary: '#27272a',      // Main borders
            secondary: '#3f3f46',    // Secondary borders
            accent: '#fbbf24',       // Accent borders
          },
          accent: {
            orange: '#fb923c',       // Dark orange accent
            gold: '#fbbf24',         // Gold accent
            cream: '#fef3c7',        // Cream accent
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans', 'sans-serif'],
        display: ['Fredoka One', 'cursive'], // Playful for children
      },
      fontSize: {
        // Adaptive text sizes for different age groups
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        // Large accessibility sizes
        '7xl': ['4.5rem', { lineHeight: '1.1' }],
        '8xl': ['6rem', { lineHeight: '1.1' }],
        '9xl': ['8rem', { lineHeight: '1.1' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '92': '23rem',
        '96': '24rem',
        '100': '25rem',
        '104': '26rem',
        '108': '27rem',
        '112': '28rem',
        '116': '29rem',
        '120': '30rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      animation: {
        'bounce-gentle': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'wiggle': 'wiggle 1s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      // Adaptive layout densities
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [
    // Role-based utility classes
    function({ addUtilities }) {
      const newUtilities = {
        '.text-scale-child': {
          'font-size': 'clamp(1.125rem, 4vw, 1.5rem)',
        },
        '.text-scale-teen': {
          'font-size': 'clamp(0.875rem, 2vw, 1rem)',
        },
        '.text-scale-parent': {
          'font-size': 'clamp(0.75rem, 1.5vw, 0.875rem)',
        },
        '.text-scale-grandparent': {
          'font-size': 'clamp(1.25rem, 5vw, 2rem)',
        },
        '.layout-spacious': {
          'gap': 'clamp(1.5rem, 4vw, 2rem)',
          'padding': 'clamp(1rem, 3vw, 1.5rem)',
        },
        '.layout-comfortable': {
          'gap': 'clamp(1rem, 2vw, 1.5rem)',
          'padding': 'clamp(0.75rem, 2vw, 1rem)',
        },
        '.layout-compact': {
          'gap': 'clamp(0.5rem, 1.5vw, 1rem)',
          'padding': 'clamp(0.5rem, 1.5vw, 0.75rem)',
        },
      };
      addUtilities(newUtilities);
    },
  ],
}