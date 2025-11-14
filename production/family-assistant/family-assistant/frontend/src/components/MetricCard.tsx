import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType<LucideIcon>;
  trend?: 'up' | 'down' | 'stable';
  color: 'blue' | 'green' | 'purple' | 'cyan' | 'red' | 'yellow';
}

const colorClasses = {
  blue: {
    bg: 'bg-ctp-blue/10',
    text: 'text-ctp-blue',
    icon: 'text-ctp-blue',
  },
  green: {
    bg: 'bg-ctp-green/10',
    text: 'text-ctp-green',
    icon: 'text-ctp-green',
  },
  purple: {
    bg: 'bg-ctp-mauve/10',
    text: 'text-ctp-mauve',
    icon: 'text-ctp-mauve',
  },
  cyan: {
    bg: 'bg-ctp-sky/10',
    text: 'text-ctp-sky',
    icon: 'text-ctp-sky',
  },
  red: {
    bg: 'bg-ctp-red/10',
    text: 'text-ctp-red',
    icon: 'text-ctp-red',
  },
  yellow: {
    bg: 'bg-ctp-yellow/10',
    text: 'text-ctp-yellow',
    icon: 'text-ctp-yellow',
  },
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
}) => {
  const colors = colorClasses[color];

  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-ctp-red" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-ctp-green" />;
    return <Minus className="w-4 h-4 text-ctp-overlay0" />;
  };

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-ctp-subtext1">{title}</p>
          <p className="text-2xl font-bold text-ctp-text">{value}</p>
          {subtitle && <p className="text-sm text-ctp-subtext0">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-3">
          {trend && (
            <div className="flex items-center gap-1">
              {getTrendIcon()}
            </div>
          )}
          <div className={`p-3 rounded-lg ${colors.bg}`}>
            <Icon className={`w-6 h-6 ${colors.icon}`} />
          </div>
        </div>
      </div>
    </div>
  );
};