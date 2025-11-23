import React from "react";

type BadgeVariant = "light" | "solid" | "default" | "secondary" | "destructive" | "outline";
type BadgeSize = "sm" | "md";
type BadgeColor =
  | "primary"
  | "success"
  | "error"
  | "warning"
  | "info"
  | "light"
  | "dark";

interface BadgeProps {
  variant?: BadgeVariant; // Badge variant
  size?: BadgeSize; // Badge size
  color?: BadgeColor; // Badge color
  startIcon?: React.ReactNode; // Icon at the start
  endIcon?: React.ReactNode; // Icon at the end
  children: React.ReactNode; // Badge content
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  variant = "light",
  color = "primary",
  size = "md",
  startIcon,
  endIcon,
  children,
  className = '',
}) => {
  const baseStyles =
    "inline-flex items-center px-2.5 py-0.5 justify-center gap-1 rounded-full font-medium";

  // Define size styles
  const sizeStyles = {
    sm: "text-theme-xs", // Smaller padding and font size
    md: "text-sm", // Default padding and font size
  };

  // Define color styles for variants
  const variants = {
    light: {
      primary:
        "bg-brand-50 text-brand-500 dark:bg-brand-500/15 dark:text-brand-400",
      success:
        "bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500",
      error:
        "bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-500",
      warning:
        "bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-orange-400",
      info: "bg-blue-light-50 text-blue-light-500 dark:bg-blue-light-500/15 dark:text-blue-light-500",
      light: "bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-white/80",
      dark: "bg-gray-500 text-white dark:bg-white/5 dark:text-white",
    },
    solid: {
      primary: "bg-brand-500 text-white dark:text-white",
      success: "bg-success-500 text-white dark:text-white",
      error: "bg-error-500 text-white dark:text-white",
      warning: "bg-warning-500 text-white dark:text-white",
      info: "bg-blue-light-500 text-white dark:text-white",
      light: "bg-gray-400 dark:bg-white/5 text-white dark:text-white/80",
      dark: "bg-gray-700 text-white dark:text-white",
    },
    default: {
      primary: "bg-blue-600 text-white",
      secondary: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
      destructive: "bg-red-600 text-white",
      outline: "border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
    },
    secondary: {
      primary: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
      secondary: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
      destructive: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
      outline: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
    },
    destructive: {
      primary: "bg-red-600 text-white",
      secondary: "bg-red-600 text-white",
      destructive: "bg-red-600 text-white",
      outline: "bg-red-600 text-white",
    },
    outline: {
      primary: "border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
      secondary: "border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
      destructive: "border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
      outline: "border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
    },
  };

  // Get styles based on size and color variant
  const sizeClass = sizeStyles[size];

  // Simplified color mapping
  const getColorClass = () => {
    switch (variant) {
      case 'default':
        return 'bg-blue-600 text-white';
      case 'secondary':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
      case 'destructive':
        return 'bg-red-600 text-white';
      case 'outline':
        return 'border border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200';
      default:
        return 'bg-blue-600 text-white';
    }
  };

  const colorStyles = getColorClass();

  return (
    <span className={`${baseStyles} ${sizeClass} ${colorStyles} ${className}`}>
      {startIcon && <span className="mr-1">{startIcon}</span>}
      {children}
      {endIcon && <span className="ml-1">{endIcon}</span>}
    </span>
  );
};

export { Badge };
export default Badge;
