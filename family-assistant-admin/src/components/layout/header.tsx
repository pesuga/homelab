"use client";

import React from "react";
import { BellIcon, MagnifyingGlassIcon, Bars3Icon } from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";
import ThemePicker from "@/components/ui/theme-picker";

interface HeaderProps {
  onMobileMenuToggle?: () => void;
  sidebarCollapsed?: boolean;
  className?: string;
}

export default function Header({ onMobileMenuToggle, sidebarCollapsed = false, className }: HeaderProps) {
  return (
    <header
      className={cn(
        "h-16 border-b border-border bg-background backdrop-blur supports-[backdrop-filter]:bg-background/80",
        className
      )}
    >
      <div className="flex h-full items-center justify-between px-4 lg:px-6">
        {/* Left side - Mobile menu toggle and search */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Mobile menu toggle */}
          <button
            onClick={onMobileMenuToggle}
            className="p-2 rounded-lg hover:bg-accent transition-colors lg:hidden flex-shrink-0"
          >
            <Bars3Icon className="w-5 h-5 text-muted-foreground" />
          </button>

          {/* Search bar */}
          <div className="relative max-w-md flex-1 hidden lg:block">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search features, settings, or help..."
              className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all"
            />
          </div>
        </div>

        {/* Right side - Notifications, theme picker, user */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Theme picker */}
          <ThemePicker />

          {/* Notifications */}
          <button className="relative p-2 rounded-lg hover:bg-accent transition-colors">
            <BellIcon className="w-5 h-5 text-muted-foreground" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full"></span>
          </button>

          {/* User avatar */}
          <div className="flex items-center gap-3 pl-3 ml-2 border-l border-border">
            <div className="text-right hidden sm:block min-w-0">
              <p className="text-sm font-medium text-foreground truncate">Admin User</p>
              <p className="text-xs text-muted-foreground truncate">Administrator</p>
            </div>
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-medium text-primary-foreground">A</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}