"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  HomeIcon,
  UserGroupIcon,
  CogIcon,
  ChartBarIcon,
  DocumentTextIcon,
  BellIcon,
  ShieldCheckIcon,
  ArchiveBoxIcon,
  ArrowRightOnRectangleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon,
} from "@heroicons/react/24/outline";

interface NavigationItem {
  id: string;
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  current?: boolean;
}

const navigation: NavigationItem[] = [
  { id: "dashboard", name: "Dashboard", href: "/", icon: HomeIcon },
  { id: "family", name: "Family Management", href: "/family", icon: UserGroupIcon },
  { id: "assistant", name: "Assistant Config", href: "/assistant", icon: CogIcon },
  { id: "memory", name: "Memory Browser", href: "/memory", icon: ArchiveBoxIcon },
  { id: "prompts", name: "Prompt Library", href: "/prompts", icon: DocumentTextIcon },
  { id: "analytics", name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { id: "alerts", name: "Alerts", href: "/alerts", icon: BellIcon },
  { id: "settings", name: "Settings", href: "/settings", icon: ShieldCheckIcon },
];

interface SidebarProps {
  className?: string;
  collapsed?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ className, collapsed = false, onToggle }: SidebarProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(collapsed);
  const pathname = usePathname();

  // Use external state if provided
  const isCollapsed = collapsed !== undefined ? collapsed : sidebarCollapsed;
  const handleToggle = onToggle || (() => setSidebarCollapsed(!sidebarCollapsed));

  return (
    <div
      className={cn(
        "flex h-full bg-gradient-to-b from-card to-secondary/10 border-r border-border transition-all duration-300 ease-in-out shadow-lg",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Sidebar content */}
      <div className="flex flex-col h-full">
        {/* Logo/Brand area */}
        <div className="flex items-center justify-between p-4">
          {!isCollapsed && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <ShieldCheckIcon className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-foreground">
                  Family Assistant
                </h1>
                <p className="text-xs text-muted-foreground">Admin Panel</p>
              </div>
            </div>
          )}
          <button
            onClick={handleToggle}
            className="p-1.5 rounded-lg hover:bg-accent transition-colors"
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronLeftIcon className="w-5 h-5 text-muted-foreground" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <item.icon
                  className={cn(
                    "w-5 h-5 flex-shrink-0",
                    isActive
                      ? "text-primary-foreground"
                      : "text-muted-foreground group-hover:text-foreground"
                  )}
                />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
                {/* Tooltip for collapsed state */}
                {isCollapsed && (
                  <div className="absolute left-16 invisible group-hover:visible bg-popover border border-border rounded-md px-2 py-1 text-sm text-popover-foreground shadow-lg whitespace-nowrap z-50">
                    {item.name}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User area */}
        <div className="p-4">
          {!isCollapsed ? (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-primary-foreground">A</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  Admin User
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  admin@homelab.local
                </p>
              </div>
              <button className="p-1.5 rounded-md hover:bg-accent transition-colors">
                <ArrowRightOnRectangleIcon className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-primary-foreground">A</span>
              </div>
              <button className="p-1.5 rounded-md hover:bg-accent transition-colors">
                <ArrowRightOnRectangleIcon className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}