import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon, Monitor } from 'lucide-react';

const ThemeToggle: React.FC = () => {
  const { theme, isDark, toggleTheme } = useTheme();

  const getIcon = () => {
    switch (theme) {
      case 'light': return <Sun className="w-4 h-4" />;
      case 'dark': return <Moon className="w-4 h-4" />;
      case 'auto': return <Monitor className="w-4 h-4" />;
      default: return <Sun className="w-4 h-4" />;
    }
  };

  const getLabel = () => {
    switch (theme) {
      case 'light': return 'Light Mode';
      case 'dark': return 'Dark Mode';
      case 'auto': return 'Auto (System)';
      default: return 'Light Mode';
    }
  };

  const getThemeInfo = () => {
    switch (theme) {
      case 'light': return 'Always light theme';
      case 'dark': return 'Always dark theme';
      case 'auto': return `Follows system (${isDark ? 'dark' : 'light'})`;
      default: return 'Always light theme';
    }
  };

  return (
    <div className="relative">
      <button
        onClick={toggleTheme}
        className={`
          relative p-2 rounded-lg transition-all duration-200
          ${isDark
            ? 'bg-gray-800 text-yellow-400 hover:bg-gray-700 border border-gray-700'
            : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200 shadow-sm'
          }
        `}
        title={`${getLabel()} - ${getThemeInfo()}`}
        aria-label={`Theme: ${getLabel()}. Current: ${getThemeInfo()}. Click to cycle through themes.`}
      >
        <div className="flex items-center gap-2">
          {getIcon()}
        </div>

        {/* Theme indicator dot */}
        <div className={`
          absolute top-1 right-1 w-2 h-2 rounded-full
          ${theme === 'light' ? 'bg-blue-500' : ''}
          ${theme === 'dark' ? 'bg-purple-500' : ''}
          ${theme === 'auto' ? 'bg-green-500' : ''}
        `} />
      </button>

      {/* Tooltip */}
      <div className={`
        absolute right-0 top-full mt-2 px-3 py-2 text-sm rounded-lg shadow-lg
        opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200
        pointer-events-none z-50 whitespace-nowrap
        ${isDark ? 'bg-gray-800 text-gray-200 border border-gray-700' : 'bg-gray-800 text-white'}
      `}>
        <div className="font-medium">{getLabel()}</div>
        <div className="text-xs opacity-75">{getThemeInfo()}</div>
        <div className="absolute -top-1 right-4 w-2 h-2 bg-gray-800 transform rotate-45"></div>
      </div>
    </div>
  );
};

export default ThemeToggle;