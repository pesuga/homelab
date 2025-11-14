import React, { useState } from 'react';
import { Palette, Check } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { catppuccin, CatppuccinFlavor } from '../styles/themes/catppuccin';

export const ThemeToggle: React.FC = () => {
  const { flavor, setFlavor } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  const flavors: Array<{ key: CatppuccinFlavor; name: string; emoji: string }> = [
    { key: 'mocha', name: 'Mocha', emoji: '🌙' },
    { key: 'macchiato', name: 'Macchiato', emoji: '🌆' },
    { key: 'frappe', name: 'Frappé', emoji: '🪴' },
    { key: 'latte', name: 'Latte', emoji: '☀️' },
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
        style={{
          backgroundColor: 'var(--ctp-surface0)',
          color: 'var(--ctp-text)',
        }}
        title="Change theme"
      >
        <Palette className="w-5 h-5" />
        <span className="text-sm font-medium">{catppuccin[flavor].name}</span>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div
            className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg z-50 border"
            style={{
              backgroundColor: 'var(--ctp-surface0)',
              borderColor: 'var(--ctp-surface2)',
            }}
          >
            <div
              className="px-3 py-2 border-b"
              style={{ borderColor: 'var(--ctp-surface2)' }}
            >
              <p
                className="text-xs font-semibold"
                style={{ color: 'var(--ctp-subtext0)' }}
              >
                Catppuccin Theme
              </p>
            </div>

            <div className="py-1">
              {flavors.map((flavorOption) => (
                <button
                  key={flavorOption.key}
                  onClick={() => {
                    setFlavor(flavorOption.key);
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm transition-colors"
                  style={{
                    backgroundColor:
                      flavor === flavorOption.key
                        ? 'var(--ctp-surface1)'
                        : 'transparent',
                    color: 'var(--ctp-text)',
                  }}
                  onMouseEnter={(e) => {
                    if (flavor !== flavorOption.key) {
                      e.currentTarget.style.backgroundColor = 'var(--ctp-surface1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (flavor !== flavorOption.key) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <span className="flex items-center gap-2">
                    <span>{flavorOption.emoji}</span>
                    <span>{flavorOption.name}</span>
                  </span>
                  {flavor === flavorOption.key && (
                    <Check className="w-4 h-4" style={{ color: 'var(--ctp-green)' }} />
                  )}
                </button>
              ))}
            </div>

            <div
              className="px-3 py-2 border-t text-xs"
              style={{
                borderColor: 'var(--ctp-surface2)',
                color: 'var(--ctp-subtext1)',
              }}
            >
              <a
                href="https://github.com/catppuccin/catppuccin"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
                style={{ color: 'var(--ctp-blue)' }}
              >
                About Catppuccin →
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
