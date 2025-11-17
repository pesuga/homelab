"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
  UserGroupIcon,
  CpuChipIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: {
    value: string;
    type: "increase" | "decrease" | "neutral";
  };
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  className?: string;
  index: number;
}

function StatCard({ title, value, change, icon: Icon, description, className, index }: StatCardProps) {
  return (
    <div className={cn("card", className)}>
      <div className="card-content">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-semibold text-foreground mt-1 break-words">{value}</p>
            {change && (
              <p className={cn(
                "text-sm mt-1.5 flex items-center gap-1",
                change.type === "increase" && "text-green-600 dark:text-green-400",
                change.type === "decrease" && "text-red-600 dark:text-red-400",
                change.type === "neutral" && "text-muted-foreground"
              )}>
                {change.value}
              </p>
            )}
            {description && (
              <p className="text-xs text-muted-foreground mt-2 leading-tight">{description}</p>
            )}
          </div>
          <div className={cn(
            "p-3 rounded-lg bg-gradient-to-br shadow-sm flex-shrink-0",
            index === 0 && "from-blue-500/10 to-blue-600/10 text-blue-600 border border-blue-200/50",
            index === 1 && "from-purple-500/10 to-purple-600/10 text-purple-600 border border-purple-200/50",
            index === 2 && "from-emerald-500/10 to-emerald-600/10 text-emerald-600 border border-emerald-200/50",
            index === 3 && "from-amber-500/10 to-amber-600/10 text-amber-600 border border-amber-200/50"
          )}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
  );
}

interface StatsGridProps {
  className?: string;
}

export default function StatsGrid({ className }: StatsGridProps) {
  const stats = [
    {
      title: "Family Members",
      value: 4,
      icon: UserGroupIcon,
      description: "2 parents, 2 children",
    },
    {
      title: "System Services",
      value: 8,
      change: { value: "All operational", type: "neutral" },
      icon: ServerIcon,
      description: "Core services running",
    },
    {
      title: "GPU Usage",
      value: "67%",
      change: { value: "+12% from yesterday", type: "increase" },
      icon: CpuChipIcon,
      description: "AMD RX 7800 XT",
    },
    {
      title: "Assistant Health",
      value: "Healthy",
      change: { value: "No issues", type: "neutral" },
      icon: CheckCircleIcon,
      description: "All systems operational",
    },
  ];

  return (
    <div className={cn(
      "grid gap-4 md:grid-cols-2 lg:grid-cols-4",
      className
    )}>
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} index={index} />
      ))}
    </div>
  );
}