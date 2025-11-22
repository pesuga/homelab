"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";

interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  voiceNavigation: boolean;
  simpleLanguage: boolean;
  colorBlindMode: "none" | "protanopia" | "deuteranopia" | "tritanopia";
  focusVisible: boolean;
  dyslexiaFont: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  updateSettings: (settings: Partial<AccessibilitySettings>) => void;
  announceToScreenReader: (message: string) => void;
}

const AccessibilityContext = React.createContext<AccessibilityContextType | null>(null);

export function useAccessibility() {
  const context = React.useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityWrapper');
  }
  return context;
}

interface AccessibilityWrapperProps {
  children: React.ReactNode;
}

export default function AccessibilityWrapper({ children }: AccessibilityWrapperProps) {
  const { user } = useAuth();
  const [settings, setSettings] = useState<AccessibilitySettings>({
    highContrast: false,
    largeText: false,
    reducedMotion: false,
    screenReader: false,
    keyboardNavigation: true,
    voiceNavigation: false,
    simpleLanguage: false,
    colorBlindMode: "none",
    focusVisible: true,
    dyslexiaFont: false
  });

  const [announcement, setAnnouncement] = useState("");
  const announcementRef = useRef<HTMLDivElement>(null);

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibility-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
      } catch (error) {
        console.error('Failed to parse accessibility settings:', error);
      }
    }

    // Apply role-based default settings
    if (user?.role) {
      const roleDefaults = {
        grandparent: {
          largeText: true,
          highContrast: true,
          reducedMotion: true,
          simpleLanguage: true
        },
        child: {
          largeText: true,
          simpleLanguage: true,
          focusVisible: true
        }
      };

      if (roleDefaults[user.role as keyof typeof roleDefaults]) {
        setSettings(prev => ({
          ...prev,
          ...roleDefaults[user.role as keyof typeof roleDefaults]
        }));
      }
    }
  }, [user?.role]);

  // Save settings to localStorage
  const updateSettings = (newSettings: Partial<AccessibilitySettings>) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);
    localStorage.setItem('accessibility-settings', JSON.stringify(updated));
  };

  // Screen reader announcements
  const announceToScreenReader = (message: string) => {
    setAnnouncement(message);
    setTimeout(() => setAnnouncement(""), 100);
  };

  // Keyboard navigation
  useEffect(() => {
    if (!settings.keyboardNavigation) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip navigation
      if (event.altKey && event.key === 's') {
        event.preventDefault();
        announceToScreenReader('Skip to main content');
        const main = document.querySelector('main');
        main?.focus();
      }

      // Accessibility menu
      if (event.altKey && event.key === 'a') {
        event.preventDefault();
        announceToScreenReader('Accessibility menu opened');
        // Toggle accessibility panel
      }

      // Voice navigation toggle
      if (event.altKey && event.key === 'v') {
        event.preventDefault();
        updateSettings({ voiceNavigation: !settings.voiceNavigation });
        announceToScreenReader(`Voice navigation ${!settings.voiceNavigation ? 'enabled' : 'disabled'}`);
      }

      // Help
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        announceToScreenReader('Help menu opened');
        // Open help modal
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [settings.keyboardNavigation, settings.voiceNavigation]);

  // Apply CSS classes based on settings
  useEffect(() => {
    const root = document.documentElement;

    // Remove all accessibility classes first
    root.classList.remove(
      'high-contrast',
      'large-text',
      'reduced-motion',
      'simple-language',
      'dyslexia-font',
      'keyboard-nav',
      'focus-visible',
      'colorblind-protanopia',
      'colorblind-deuteranopia',
      'colorblind-tritanopia'
    );

    // Apply settings
    if (settings.highContrast) root.classList.add('high-contrast');
    if (settings.largeText) root.classList.add('large-text');
    if (settings.reducedMotion) root.classList.add('reduced-motion');
    if (settings.simpleLanguage) root.classList.add('simple-language');
    if (settings.dyslexiaFont) root.classList.add('dyslexia-font');
    if (settings.keyboardNavigation) root.classList.add('keyboard-nav');
    if (settings.focusVisible) root.classList.add('focus-visible');

    if (settings.colorBlindMode !== 'none') {
      root.classList.add(`colorblind-${settings.colorBlindMode}`);
    }

    // ARIA attributes
    root.setAttribute('data-accessibility', JSON.stringify(settings));
  }, [settings]);

  // Generate CSS variables for dynamic styling
  const cssVariables = {
    '--text-scale': settings.largeText ? '1.2' : '1',
    '--contrast-multiplier': settings.highContrast ? '1.5' : '1',
    '--animation-duration': settings.reducedMotion ? '0.01s' : '0.3s',
    '--border-width': settings.focusVisible ? '3px' : '2px',
    '--font-family': settings.dyslexiaFont ? "'OpenDyslexic', 'Comic Sans MS', sans-serif" : "inherit"
  };

  return (
    <AccessibilityContext.Provider value={{ settings, updateSettings, announceToScreenReader }}>
      <div style={cssVariables} className={`accessibility-wrapper ${settings.screenReader ? 'screen-reader-enabled' : ''}`}>
        {/* Screen reader announcements */}
        <div
          ref={announcementRef}
          className="sr-only"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {announcement}
        </div>

        {/* Skip to main content link */}
        {settings.keyboardNavigation && (
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-lg z-50 focus:outline-none focus:ring-4 focus:ring-blue-300"
            onClick={(e) => {
              e.preventDefault();
              const main = document.getElementById('main-content');
              main?.focus();
            }}
          >
            Skip to main content
          </a>
        )}

        {/* Accessibility controls (floating button) */}
        <div className="fixed bottom-4 right-4 z-40">
          <button
            onClick={() => announceToScreenReader('Accessibility panel opened')}
            className="w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-4 focus:ring-blue-300"
            aria-label="Accessibility options"
            title="Accessibility options (Alt+A)"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Main content */}
        <main id="main-content" role="main" tabIndex={-1}>
          {children}
        </main>

        {/* Accessibility styles */}
        <style jsx>{`
          .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
          }

          /* High Contrast Mode */
          .high-contrast {
            --bg-primary: #000000 !important;
            --bg-secondary: #1a1a1a !important;
            --text-primary: #ffffff !important;
            --text-secondary: #cccccc !important;
            --border-color: #ffffff !important;
            --accent-color: #ffff00 !important;
          }

          /* Large Text */
          .large-text {
            font-size: calc(1rem * var(--text-scale));
            line-height: 1.6;
          }

          .large-text h1 { font-size: calc(2rem * var(--text-scale)); }
          .large-text h2 { font-size: calc(1.5rem * var(--text-scale)); }
          .large-text h3 { font-size: calc(1.25rem * var(--text-scale)); }
          .large-text button { font-size: calc(1rem * var(--text-scale)); }

          /* Reduced Motion */
          .reduced-motion * {
            animation-duration: var(--animation-duration) !important;
            transition-duration: var(--animation-duration) !important;
          }

          /* Dyslexia Font */
          .dyslexia-font {
            font-family: var(--font-family) !important;
            letter-spacing: 0.1em;
            line-height: 1.8;
          }

          /* Focus Visible */
          .focus-visible *:focus {
            outline: var(--border-width) solid #0000ff !important;
            outline-offset: 2px !important;
          }

          .high-contrast .focus-visible *:focus {
            outline-color: #ffff00 !important;
          }

          /* Color Blind Modes */
          .colorblind-protanopia {
            filter: url(#protanopia-filter);
          }

          .colorblind-deuteranopia {
            filter: url(#deuteranopia-filter);
          }

          .colorblind-tritanopia {
            filter: url(#tritanopia-filter);
          }

          /* Keyboard Navigation */
          .keyboard-nav *:focus {
            outline: 2px solid #0066cc;
            outline-offset: 2px;
          }

          /* Simple Language Indicators */
          .simple-language .complex-term {
            border-bottom: 2px dotted #666;
            cursor: help;
          }

          .simple-language .tooltip {
            background: #f0f0f0;
            border: 1px solid #ccc;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.9em;
            max-width: 200px;
          }
        `}</style>

        {/* SVG filters for color blindness */}
        <svg style={{ display: 'none' }}>
          <defs>
            <filter id="protanopia-filter">
              <feColorMatrix type="matrix" values="
                0.567, 0.433, 0,     0, 0
                0.558, 0.442, 0,     0, 0
                0,     0.242, 0.758, 0, 0
                0,     0,     0,     1, 0
              "/>
            </filter>
            <filter id="deuteranopia-filter">
              <feColorMatrix type="matrix" values="
                0.625, 0.375, 0,   0, 0
                0.7,   0.3,   0,   0, 0
                0,     0.3,   0.7, 0, 0
                0,     0,     0,   1, 0
              "/>
            </filter>
            <filter id="tritanopia-filter">
              <feColorMatrix type="matrix" values="
                0.95, 0.05,  0,     0, 0
                0,    0.433, 0.567, 0, 0
                0,    0.475, 0.525, 0, 0
                0,    0,     0,     1, 0
              "/>
            </filter>
          </defs>
        </svg>
      </div>
    </AccessibilityContext.Provider>
  );
}

// Accessibility helper components
export function AccessibleButton({
  children,
  onClick,
  ariaLabel,
  ariaDescribedBy,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  ariaLabel?: string;
  ariaDescribedBy?: string;
}) {
  const { announceToScreenReader } = useAccessibility();

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (onClick) {
      onClick(event);
    }
    // Announce action to screen reader
    const buttonText = typeof children === 'string' ? children : 'Button';
    announceToScreenReader(`${buttonText} activated`);
  };

  return (
    <button
      onClick={handleClick}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      {...props}
    >
      {children}
    </button>
  );
}

export function AccessibleInput({
  label,
  error,
  helpText,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  helpText?: string;
}) {
  const { announceToScreenReader } = useAccessibility();
  const inputId = `input-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = error ? `${inputId}-error` : undefined;
  const helpId = helpText ? `${inputId}-help` : undefined;

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (props.onChange) {
      props.onChange(event);
    }
    announceToScreenReader(`${label}: ${event.target.value}`);
  };

  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={inputId}
        aria-describedby={[helpId, errorId].filter(Boolean).join(' ') || undefined}
        aria-invalid={error ? 'true' : 'false'}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        {...props}
      />
      {helpText && (
        <p id={helpId} className="text-sm text-gray-500">
          {helpText}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

// Voice navigation hook
export function useVoiceNavigation() {
  const { settings, announceToScreenReader } = useAccessibility();

  const speak = (text: string) => {
    if ('speechSynthesis' in window && settings.voiceNavigation) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      speechSynthesis.speak(utterance);
    }
  };

  const announce = (text: string) => {
    announceToScreenReader(text);
    speak(text);
  };

  return { speak, announce };
}