"use client";

import React, { useState, useEffect } from "react";
import { CheckIcon, ComputerDesktopIcon } from "@heroicons/react/24/outline";
import { useTheme } from "@/contexts/theme-context";
import { CatppuccinTheme, CatppuccinThemeConfig } from "@/types/theme";

interface ThemeOption {
  theme: CatppuccinTheme;
  config: CatppuccinThemeConfig;
  isSystem?: boolean;
}

export default function ThemePicker() {
  const { theme, setTheme, themes, isSystem, setSystem } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  // Close dropdown on escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen]);

  const options: ThemeOption[] = [
    ...themes.map(config => ({ theme: config.name, config })),
    { theme: 'system' as CatppuccinTheme, config: null as any, isSystem: true }
  ];

  const currentOption = isSystem
    ? options.find(opt => opt.isSystem)
    : options.find(opt => opt.theme === theme);

  const handleSelect = (option: ThemeOption) => {
    if (option.isSystem) {
      setSystem(true);
    } else {
      setTheme(option.theme);
    }
    setIsOpen(false);
  };

  const getThemePreview = (config: CatppuccinThemeConfig | null) => {
    if (!config) {
      return (
        <div className="w-4 h-4 rounded border border-border flex items-center justify-center">
          <ComputerDesktopIcon className="w-3 h-3 text-muted-foreground" />
        </div>
      );
    }

    return (
      <div className="w-4 h-4 rounded-full border-2"
           style={{
             backgroundColor: `hsl(${config.colors.base})`,
             borderColor: `hsl(${config.colors.surface0})`
           }}>
        <div className="w-2 h-2 rounded-full mt-0.5 ml-0.5"
             style={{ backgroundColor: `hsl(${config.colors.text})` }} />
      </div>
    );
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent transition-colors"
        title="Change theme"
      >
        <div className="w-5 h-5 flex items-center justify-center">
          {getThemePreview(currentOption?.config || null)}
        </div>
        <span className="text-sm text-muted-foreground min-w-0 text-left">
          {currentOption?.isSystem ? 'System' : currentOption?.config?.displayName}
        </span>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-1 z-50 min-w-[200px] rounded-lg border border-border bg-popover theme-dropdown dropdown-menu">
            <div className="p-1">
              {options.map((option) => {
                const isSelected = option.isSystem ? isSystem : theme === option.theme;

                return (
                  <button
                    key={option.isSystem ? 'system' : option.theme}
                    onClick={() => handleSelect(option)}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors hover:bg-accent/80 focus:bg-accent focus:outline-none relative z-10"
                  >
                    <div className="w-5 h-5 flex items-center justify-center">
                      {getThemePreview(option.config)}
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium text-popover-foreground">
                        {option.isSystem ? 'System' : option.config.displayName}
                      </div>
                      {!option.isSystem && (
                        <div className="text-xs text-muted-foreground">
                          {option.config.isDark ? 'Dark' : 'Light'}
                        </div>
                      )}
                    </div>
                    {isSelected && (
                      <CheckIcon className="w-4 h-4 text-primary" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}