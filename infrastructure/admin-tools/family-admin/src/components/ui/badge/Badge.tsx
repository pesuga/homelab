import React from "react";

type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info";
type BadgeSize = "sm" | "md";

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  size = "md",
  startIcon,
  endIcon,
  children,
  className = '',
}) => {
  const baseStyles =
    "inline-flex items-center justify-center gap-1 rounded-full font-medium transition-colors";

  // Define size styles with standard Tailwind classes
  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs", // Smaller padding and font size
    md: "px-2.5 py-0.5 text-sm", // Default padding and font size
  };

  // Define variant styles with standard Tailwind classes
  const variantStyles = {
    default: "bg-blue-100 text-blue-800 border border-blue-200",
    secondary: "bg-gray-100 text-gray-800 border border-gray-200",
    destructive: "bg-red-100 text-red-800 border border-red-200",
    outline: "border border-gray-300 bg-white text-gray-700",
    success: "bg-green-100 text-green-800 border border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border border-yellow-200",
    info: "bg-cyan-100 text-cyan-800 border border-cyan-200",
  };

  // Dark mode styles
  const darkModeStyles = {
    default: "dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700",
    secondary: "dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
    destructive: "dark:bg-red-900/30 dark:text-red-300 dark:border-red-700",
    outline: "dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200",
    success: "dark:bg-green-900/30 dark:text-green-300 dark:border-green-700",
    warning: "dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-700",
    info: "dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-700",
  };

  const sizeClass = sizeStyles[size];
  const variantClass = variantStyles[variant] || variantStyles.default;
  const darkModeClass = darkModeStyles[variant] || darkModeStyles.default;

  return (
    <span className={`${baseStyles} ${sizeClass} ${variantClass} ${darkModeClass} ${className}`}>
      {startIcon && <span className="mr-1">{startIcon}</span>}
      {children}
      {endIcon && <span className="ml-1">{endIcon}</span>}
    </span>
  );
};

export { Badge };
export default Badge;
