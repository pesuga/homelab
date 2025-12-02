"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";

// Types
interface FamilyMember {
  id: string;
  name: string;
  role: "parent" | "teenager" | "child" | "grandparent";
  status: "online" | "offline" | "busy" | "school" | "work" | "sleeping";
  avatar?: string;
  activity?: string;
  location?: string;
  lastSeen?: Date;
  screenTime?: {
    today: number; // minutes
    weekly: number; // minutes
    limit?: number; // daily limit in minutes
  };
  deviceInfo?: {
    type: "phone" | "tablet" | "computer" | "smartwatch";
    battery?: number;
    app?: string;
  };
}

interface Activity {
  id: string;
  memberId: string;
  type: "homework" | "chore" | "appointment" | "reminder" | "location_change" | "app_usage";
  title: string;
  timestamp: Date;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  metadata?: {
    dueTime?: Date;
    location?: string;
    duration?: number; // minutes
    priority?: "low" | "medium" | "high";
    completedBy?: string;
  };
}

interface LocationAlert {
  id: string;
  memberId: string;
  type: "arrival" | "departure" | "geofence_entry" | "geofence_exit";
  location: string;
  timestamp: Date;
  message: string;
}

interface SystemHealth {
  status: "healthy" | "warning" | "critical";
  services: {
    nexus: { status: string; uptime: number };
    database: { status: string; connections: number };
    storage: { used: number; total: number };
    network: { status: string; bandwidth: number };
  };
  alerts: Array<{
    id: string;
    level: "info" | "warning" | "error";
    message: string;
    timestamp: Date;
  }>;
}

export default function FamilyDashboard() {
  const { user } = useAuth();
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [locationAlerts, setLocationAlerts] = useState<LocationAlert[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMember, setSelectedMember] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "members" | "activities" | "locations" | "settings">("overview");

  // Check if user is a parent (only parents can see this dashboard)
  if (user?.role !== "parent" && !user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Access Restricted
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            This dashboard is only available for family administrators.
          </p>
        </div>
      </div>
    );
  }

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Mock data - replace with actual API calls
        const mockFamilyMembers: FamilyMember[] = [
          {
            id: "1",
            name: "Sarah",
            role: "parent",
            status: "work",
            activity: "In a meeting",
            location: "Downtown Office",
            lastSeen: new Date(),
            deviceInfo: {
              type: "computer",
              battery: 85,
              app: "Video Conference"
            }
          },
          {
            id: "2",
            name: "Alex",
            role: "teenager",
            status: "school",
            activity: "Math class",
            location: "Lincoln High School",
            lastSeen: new Date(Date.now() - 30 * 60000),
            screenTime: {
              today: 145,
              weekly: 890,
              limit: 180
            },
            deviceInfo: {
              type: "phone",
              battery: 62,
              app: "Educational App"
            }
          },
          {
            id: "3",
            name: "Emma",
            role: "child",
            status: "school",
            activity: "Art class",
            location: "Lincoln Elementary",
            lastSeen: new Date(Date.now() - 45 * 60000),
            screenTime: {
              today: 65,
              weekly: 320,
              limit: 120
            },
            deviceInfo: {
              type: "tablet",
              battery: 78,
              app: "Drawing App"
            }
          },
          {
            id: "4",
            name: "Robert",
            role: "grandparent",
            status: "online",
            activity: "Reading news",
            location: "Home",
            lastSeen: new Date(Date.now() - 15 * 60000),
            deviceInfo: {
              type: "tablet",
              battery: 45,
              app: "News App"
            }
          }
        ];

        const mockActivities: Activity[] = [
          {
            id: "1",
            memberId: "2",
            type: "homework",
            title: "Math homework - Chapter 5 completed",
            timestamp: new Date(Date.now() - 2 * 60 * 60000),
            status: "completed",
            metadata: {
              duration: 45,
              priority: "high",
              completedBy: "Alex"
            }
          },
          {
            id: "2",
            memberId: "3",
            type: "chore",
            title: "Clean your room",
            timestamp: new Date(Date.now() - 30 * 60000),
            status: "in_progress",
            metadata: {
              priority: "medium"
            }
          },
          {
            id: "3",
            memberId: "4",
            type: "appointment",
            title: "Doctor appointment",
            timestamp: new Date(Date.now() + 3 * 60 * 60000),
            status: "pending",
            metadata: {
              dueTime: new Date(Date.now() + 3 * 60 * 60000),
              location: "Medical Center",
              priority: "high"
            }
          },
          {
            id: "4",
            memberId: "1",
            type: "location_change",
            title: "Arrived at work",
            timestamp: new Date(Date.now() - 4 * 60 * 60000),
            status: "completed",
            metadata: {
              location: "Downtown Office"
            }
          }
        ];

        const mockLocationAlerts: LocationAlert[] = [
          {
            id: "1",
            memberId: "2",
            type: "arrival",
            location: "Lincoln High School",
            timestamp: new Date(Date.now() - 8 * 60 * 60000),
            message: "Alex arrived at school"
          },
          {
            id: "2",
            memberId: "3",
            type: "geofence_exit",
            location: "Home Zone",
            timestamp: new Date(Date.now() - 15 * 60 * 60000),
            message: "Emma left the home area"
          }
        ];

        const mockSystemHealth: SystemHealth = {
          status: "healthy",
          services: {
            nexus: { status: "online", uptime: 99.8 },
            database: { status: "connected", connections: 12 },
            storage: { used: 2.3, total: 10 },
            network: { status: "optimal", bandwidth: 145 }
          },
          alerts: [
            {
              id: "1",
              level: "info",
              message: "Weekly backup completed successfully",
              timestamp: new Date(Date.now() - 2 * 60 * 60000)
            }
          ]
        };

        setFamilyMembers(mockFamilyMembers);
        setRecentActivities(mockActivities);
        setLocationAlerts(mockLocationAlerts);
        setSystemHealth(mockSystemHealth);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Get member by ID
  const getMemberById = (id: string) => familyMembers.find(member => member.id === id);

  // Format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  };

  // Format relative time
  const formatRelativeTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  // Get status color
  const getStatusColor = (status: string) => {
    const colors = {
      online: "bg-green-500",
      offline: "bg-gray-400",
      busy: "bg-red-500",
      school: "bg-blue-500",
      work: "bg-purple-500",
      sleeping: "bg-indigo-500"
    };
    return colors[status as keyof typeof colors] || "bg-gray-400";
  };

  // Get priority color
  const getPriorityColor = (priority?: string) => {
    const colors = {
      high: "text-red-600 bg-red-100 border-red-200",
      medium: "text-yellow-600 bg-yellow-100 border-yellow-200",
      low: "text-green-600 bg-green-100 border-green-200"
    };
    return colors[priority as keyof typeof colors] || colors.low;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Family Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Real-time overview of your family's activities and well-being
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* System Status */}
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            systemHealth?.status === "healthy"
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : systemHealth?.status === "warning"
              ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
          }`}>
            {systemHealth?.status === "healthy" ? "All Systems OK" :
             systemHealth?.status === "warning" ? "Some Issues" : "Critical Issues"}
          </div>

          {/* Last Updated */}
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {formatRelativeTime(new Date())}
          </div>
        </div>
      </div>

      {/* Alert Banner */}
      {locationAlerts.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Recent Location Updates
              </p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                {locationAlerts[0].message} • {formatRelativeTime(locationAlerts[0].timestamp)}
              </p>
            </div>
            <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
              View All
            </button>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {[
            { id: "overview", label: "Overview", icon: "🏠" },
            { id: "members", label: "Members", icon: "👥" },
            { id: "activities", label: "Activities", icon: "📋" },
            { id: "locations", label: "Locations", icon: "📍" },
            { id: "settings", label: "Settings", icon: "⚙️" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Family Status Cards */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            {familyMembers.map((member) => (
              <div
                key={member.id}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedMember(member.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                        {member.name[0]}
                      </div>
                      <div className={`absolute -bottom-1 -right-1 w-4 h-4 ${getStatusColor(member.status)} rounded-full border-2 border-white dark:border-gray-800`}></div>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{member.name}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{member.role}</p>
                    </div>
                  </div>

                  {member.deviceInfo && (
                    <div className="text-right">
                      <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                        {member.deviceInfo.type}
                      </div>
                      {member.deviceInfo.battery && (
                        <div className="flex items-center space-x-1 mt-1">
                          <div className={`w-2 h-2 rounded-full ${
                            member.deviceInfo.battery > 50 ? 'bg-green-500' :
                            member.deviceInfo.battery > 20 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}></div>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {member.deviceInfo.battery}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {member.status}
                    </span>
                  </div>

                  {member.activity && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Activity:</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {member.activity}
                      </span>
                    </div>
                  )}

                  {member.location && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Location:</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {member.location}
                      </span>
                    </div>
                  )}

                  {member.screenTime && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Screen Time:</span>
                      <span className={`text-sm font-medium ${
                        member.screenTime.today > (member.screenTime.limit || 180)
                          ? 'text-red-600'
                          : member.screenTime.today > (member.screenTime.limit || 180) * 0.8
                          ? 'text-yellow-600'
                          : 'text-green-600'
                      }`}>
                        {Math.floor(member.screenTime.today / 60)}h {member.screenTime.today % 60}m
                        {member.screenTime.limit && ` / ${Math.floor(member.screenTime.limit / 60)}h`}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Quick Stats & System Health */}
          <div className="space-y-4">
            {/* Quick Stats */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Online Now</span>
                  <span className="text-lg font-bold text-green-600">
                    {familyMembers.filter(m => m.status === "online").length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">At School</span>
                  <span className="text-lg font-bold text-blue-600">
                    {familyMembers.filter(m => m.status === "school").length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">At Work</span>
                  <span className="text-lg font-bold text-purple-600">
                    {familyMembers.filter(m => m.status === "work").length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Pending Tasks</span>
                  <span className="text-lg font-bold text-orange-600">
                    {recentActivities.filter(a => a.status === "pending").length}
                  </span>
                </div>
              </div>
            </div>

            {/* System Health */}
            {systemHealth && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">System Health</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Nexus Status</span>
                    <span className="text-sm font-medium text-green-600">
                      {systemHealth.services.nexus.uptime}% Uptime
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Storage</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {systemHealth.services.storage.used}GB / {systemHealth.services.storage.total}GB
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Network</span>
                    <span className="text-sm font-medium text-green-600">
                      {systemHealth.services.network.bandwidth} Mbps
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full px-3 py-2 text-sm text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors text-left">
                  📍 Check All Locations
                </button>
                <button className="w-full px-3 py-2 text-sm text-green-600 bg-green-50 hover:bg-green-100 rounded-lg transition-colors text-left">
                  📞 Start Family Call
                </button>
                <button className="w-full px-3 py-2 text-sm text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors text-left">
                  📅 Schedule Family Meeting
                </button>
                <button className="w-full px-3 py-2 text-sm text-orange-600 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors text-left">
                  ⚠️ Emergency Alert
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "members" && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Family Members Details</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Member
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Device
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Screen Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Last Seen
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {familyMembers.map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                            {member.name[0]}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {member.name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                              {member.role}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className={`w-2 h-2 ${getStatusColor(member.status)} rounded-full mr-2`}></div>
                          <span className="text-sm text-gray-900 dark:text-white capitalize">
                            {member.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {member.location || "Unknown"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          {member.deviceInfo?.type || "No device"}
                        </div>
                        {member.deviceInfo?.battery && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {member.deviceInfo.battery}% battery
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {member.screenTime ? (
                          <div className="text-sm">
                            <span className={`font-medium ${
                              member.screenTime.today > (member.screenTime.limit || 180)
                                ? 'text-red-600'
                                : 'text-gray-900 dark:text-white'
                            }`}>
                              {Math.floor(member.screenTime.today / 60)}h {member.screenTime.today % 60}m
                            </span>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Today
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500 dark:text-gray-400">No data</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {member.lastSeen ? formatRelativeTime(member.lastSeen) : "Never"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === "activities" && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activities</h3>
            <div className="space-y-4">
              {recentActivities.map((activity) => {
                const member = getMemberById(activity.memberId);
                return (
                  <div key={activity.id} className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                      {member?.name[0]}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {activity.title}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {member?.name} • {formatRelativeTime(activity.timestamp)}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${
                            activity.status === "completed" ? "bg-green-100 text-green-800 border-green-200" :
                            activity.status === "in_progress" ? "bg-yellow-100 text-yellow-800 border-yellow-200" :
                            activity.status === "cancelled" ? "bg-red-100 text-red-800 border-red-200" :
                            "bg-gray-100 text-gray-800 border-gray-200"
                          }`}>
                            {activity.status}
                          </span>
                          {activity.metadata?.priority && (
                            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityColor(activity.metadata.priority)}`}>
                              {activity.metadata.priority}
                            </span>
                          )}
                        </div>
                      </div>
                      {activity.metadata && (
                        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                          {activity.metadata.location && (
                            <span className="mr-4">📍 {activity.metadata.location}</span>
                          )}
                          {activity.metadata.duration && (
                            <span className="mr-4">⏱️ {activity.metadata.duration} min</span>
                          )}
                          {activity.metadata.dueTime && (
                            <span>🕐 Due {formatTime(activity.metadata.dueTime)}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === "locations" && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Location History</h3>
            <div className="space-y-4">
              {locationAlerts.map((alert) => {
                const member = getMemberById(alert.memberId);
                return (
                  <div key={alert.id} className="flex items-start space-x-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {alert.message}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {member?.name} • {alert.location}
                          </p>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {formatRelativeTime(alert.timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === "settings" && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Dashboard Settings</h3>
            <div className="space-y-6">
              <div>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">Notifications</h4>
                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Location alerts</span>
                    <input type="checkbox" defaultChecked className="rounded text-blue-600" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Screen time limits</span>
                    <input type="checkbox" defaultChecked className="rounded text-blue-600" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Activity completions</span>
                    <input type="checkbox" defaultChecked className="rounded text-blue-600" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">System health alerts</span>
                    <input type="checkbox" defaultChecked className="rounded text-blue-600" />
                  </label>
                </div>
              </div>

              <div>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">Privacy</h4>
                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Location sharing</span>
                    <select className="rounded text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700">
                      <option>All family members</option>
                      <option>Parents only</option>
                      <option>Disabled</option>
                    </select>
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Activity tracking</span>
                    <select className="rounded text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700">
                      <option>All activities</option>
                      <option>Important only</option>
                      <option>Disabled</option>
                    </select>
                  </label>
                </div>
              </div>

              <div>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">Display</h4>
                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Auto-refresh</span>
                    <input type="checkbox" defaultChecked className="rounded text-blue-600" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">Refresh interval</span>
                    <select className="rounded text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700">
                      <option>30 seconds</option>
                      <option>1 minute</option>
                      <option>5 minutes</option>
                      <option>Manual</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}