import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', text = 'Thinking...' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  };

  return (
    <div className="flex items-center gap-3 mb-4">
      {/* Bot Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-blue-500 text-white">
        <svg className={`${sizeClasses[size]} animate-spin`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>

      {/* Thinking Indicator */}
      <div className="flex flex-col">
        <div className="bg-white dark:bg-gray-700 rounded-2xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-600 rounded-tl-sm">
          <div className="flex items-center gap-2">
            {/* Animated dots */}
            <div className="flex gap-1">
              <div className={`${dotSizes[size]} rounded-full bg-blue-500 animate-bounce`} style={{ animationDelay: '0ms' }}></div>
              <div className={`${dotSizes[size]} rounded-full bg-blue-500 animate-bounce`} style={{ animationDelay: '150ms' }}></div>
              <div className={`${dotSizes[size]} rounded-full bg-blue-500 animate-bounce`} style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-300">{text}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
