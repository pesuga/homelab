import MainLayout from "@/components/layout/main-layout";
import StatsGrid from "@/components/dashboard/stats-grid";
import { cn } from "@/lib/utils";
import {
  CpuChipIcon,
  ServerIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
} from "@heroicons/react/24/outline";

export default function Home() {
  const recentActivity = [
    {
      id: 1,
      type: "conversation",
      message: "Family conversation about dinner plans",
      user: "Sarah",
      time: "2 minutes ago",
      icon: ChatBubbleLeftRightIcon,
      color: "blue",
    },
    {
      id: 2,
      type: "system",
      message: "GPU memory usage optimized",
      user: "System",
      time: "15 minutes ago",
      icon: CpuChipIcon,
      color: "emerald",
    },
    {
      id: 3,
      type: "service",
      message: "Ollama service health check passed",
      user: "Monitor",
      time: "1 hour ago",
      icon: ServerIcon,
      color: "purple",
    },
    {
      id: 4,
      type: "document",
      message: "New memory entries created",
      user: "Assistant",
      time: "2 hours ago",
      icon: DocumentTextIcon,
      color: "amber",
    },
  ];

  const quickActions = [
    {
      title: "Start Conversation",
      description: "Begin a new family chat",
      icon: ChatBubbleLeftRightIcon,
      href: "/chat",
      color: "primary",
    },
    {
      title: "View Memories",
      description: "Browse conversation history",
      icon: DocumentTextIcon,
      href: "/memory",
      color: "secondary",
    },
    {
      title: "System Status",
      description: "Check service health",
      icon: ServerIcon,
      href: "/monitoring",
      color: "info",
    },
    {
      title: "AI Configuration",
      description: "Customize assistant settings",
      icon: CpuChipIcon,
      href: "/assistant",
      color: "warning",
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="pb-2">
          <h1 className="text-3xl font-bold text-foreground">
            Welcome to Family Assistant
          </h1>
          <p className="text-muted-foreground mt-2">
            Monitor and manage your family's AI assistant platform
          </p>
        </div>

        {/* Stats Grid */}
        <div className="pb-2">
          <StatsGrid />
        </div>

        {/* Quick Actions and Recent Activity */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Quick Actions */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Quick Actions</h2>
              <p className="card-description">
                Common tasks and features
              </p>
            </div>
            <div className="card-content">
              <div className="grid gap-4 sm:grid-cols-2">
                {quickActions.map((action) => (
                  <a
                    key={action.title}
                    href={action.href}
                    className="flex items-start gap-3 p-4 rounded-lg border border-border hover:bg-accent/50 transition-all duration-200 group hover:shadow-sm"
                  >
                    <div className={cn(
                      "p-3 rounded-lg group-hover:scale-105 transition-all duration-200 shadow-sm group-hover:shadow-md",
                      action.color === "primary" && "bg-gradient-to-br from-blue-500/20 to-blue-600/20 text-blue-600 border border-blue-200/50",
                      action.color === "secondary" && "bg-gradient-to-br from-purple-500/20 to-purple-600/20 text-purple-600 border border-purple-200/50",
                      action.color === "info" && "bg-gradient-to-br from-cyan-500/20 to-cyan-600/20 text-cyan-600 border border-cyan-200/50",
                      action.color === "warning" && "bg-gradient-to-br from-amber-500/20 to-amber-600/20 text-amber-600 border border-amber-200/50"
                    )}>
                      <action.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">
                        {action.title}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1 leading-tight">
                        {action.description}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recent Activity</h2>
              <p className="card-description">
                Latest system and family events
              </p>
            </div>
            <div className="card-content">
              <div className="space-y-3">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className={cn(
                      "p-2 rounded-lg shadow-sm flex-shrink-0",
                      activity.color === "blue" && "bg-gradient-to-br from-blue-500/20 to-blue-600/20 text-blue-600 border border-blue-200/50",
                      activity.color === "emerald" && "bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 text-emerald-600 border border-emerald-200/50",
                      activity.color === "purple" && "bg-gradient-to-br from-purple-500/20 to-purple-600/20 text-purple-600 border border-purple-200/50",
                      activity.color === "amber" && "bg-gradient-to-br from-amber-500/20 to-amber-600/20 text-amber-600 border border-amber-200/50"
                    )}>
                      <activity.icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground leading-tight">
                        {activity.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-xs text-muted-foreground">
                          {activity.user}
                        </span>
                        <span className="text-xs text-muted-foreground">•</span>
                        <span className="text-xs text-muted-foreground">
                          {activity.time}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* System Overview */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">System Overview</h2>
            <p className="card-description">
              Current status of all family assistant services
            </p>
          </div>
          <div className="card-content">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Ollama</span>
                  <span className="badge bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">Online</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2.5">
                  <div className="bg-green-500 h-2.5 rounded-full transition-all duration-300" style={{ width: "85%" }}></div>
                </div>
                <p className="text-xs text-muted-foreground leading-tight">GPU: 67% | Memory: 4.2GB</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Qdrant</span>
                  <span className="badge bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">Online</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2.5">
                  <div className="bg-green-500 h-2.5 rounded-full transition-all duration-300" style={{ width: "45%" }}></div>
                </div>
                <p className="text-xs text-muted-foreground leading-tight">Memory: 2.1GB | 8.5K vectors</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Redis</span>
                  <span className="badge bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">Online</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2.5">
                  <div className="bg-green-500 h-2.5 rounded-full transition-all duration-300" style={{ width: "30%" }}></div>
                </div>
                <p className="text-xs text-muted-foreground leading-tight">Memory: 245MB | 1.2K keys</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">PostgreSQL</span>
                  <span className="badge bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">Online</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2.5">
                  <div className="bg-green-500 h-2.5 rounded-full transition-all duration-300" style={{ width: "60%" }}></div>
                </div>
                <p className="text-xs text-muted-foreground leading-tight">Storage: 3.2GB | 127 connections</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
