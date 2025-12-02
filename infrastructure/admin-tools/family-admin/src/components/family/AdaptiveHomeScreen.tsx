"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/api-client";
import VoiceInterface from "./VoiceInterface";

// Types
interface FamilyMember {
  id: string;
  name: string;
  role: "parent" | "teenager" | "child" | "grandparent";
  status: "online" | "offline" | "busy" | "school" | "work" | "sleeping";
  avatar?: string;
  activity?: string;
  location?: string;
}

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  color: string;
  action: () => void;
  roles: string[];
  priority: number;
}

interface FamilyActivity {
  id: string;
  type: "homework" | "chore" | "appointment" | "reminder" | "fun";
  title: string;
  assignedTo: string[];
  dueTime?: string;
  status: "pending" | "in_progress" | "completed";
}

// Assistant Name and Configuration
const ASSISTANT_CONFIG = {
  name: "Nexus",
  wakeWord: "Hey Nexus",
  persona: {
    role: "family_coordinator",
    traits: ["caring", "organized", "supportive", "protective", "fun"],
    communicationStyle: "warm_and_welcoming"
  }
};

export default function AdaptiveHomeScreen() {
  const { user } = useAuth();
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [familyActivities, setFamilyActivities] = useState<FamilyActivity[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [loading, setLoading] = useState(true);

  // Time-based greetings
  const getGreeting = (role: string, hour: number) => {
    const timeGreeting =
      hour < 12 ? "Good morning" :
      hour < 17 ? "Good afternoon" :
      hour < 21 ? "Good evening" : "Good night";

    const roleGreetings = {
      parent: `${timeGreeting}, ${user?.first_name}! Ready to manage the family?`,
      teenager: `${timeGreeting}, ${user?.first_name}! What can I help you with today?`,
      child: `${timeGreeting}, ${user?.first_name}! Ready for some fun and learning?`,
      grandparent: `${timeGreeting}, ${user?.first_name}! How can I assist you today?`
    };

    return roleGreetings[role as keyof typeof roleGreetings] || `${timeGreeting}, ${user?.first_name}!`;
  };

  // Role-based quick actions
  const getQuickActions = (role: string): QuickAction[] => {
    const baseActions: QuickAction[] = [
      {
        id: "voice-chat",
        label: `Talk to ${ASSISTANT_CONFIG.name}`,
        icon: "mic",
        color: "bg-blue-500 hover:bg-blue-600",
        action: () => document.getElementById('voice-interface')?.scrollIntoView({ behavior: 'smooth' }),
        roles: ["parent", "teenager", "child", "grandparent"],
        priority: 1
      },
      {
        id: "family-status",
        label: "Family Status",
        icon: "users",
        color: "bg-green-500 hover:bg-green-600",
        action: () => showFamilyStatus(),
        roles: ["parent", "teenager", "child", "grandparent"],
        priority: 2
      }
    ];

    const roleSpecificActions = {
      parent: [
        {
          id: "manage-tasks",
          label: "Manage Tasks",
          icon: "checklist",
          color: "bg-purple-500 hover:bg-purple-600",
          action: () => openTaskManager(),
          roles: ["parent"],
          priority: 3
        },
        {
          id: "parental-controls",
          label: "Parental Controls",
          icon: "shield",
          color: "bg-red-500 hover:bg-red-600",
          action: () => openParentalControls(),
          roles: ["parent"],
          priority: 4
        },
        {
          id: "family-calendar",
          label: "Family Calendar",
          icon: "calendar",
          color: "bg-indigo-500 hover:bg-indigo-600",
          action: () => openFamilyCalendar(),
          roles: ["parent"],
          priority: 5
        }
      ],
      teenager: [
        {
          id: "homework-help",
          label: "Homework Help",
          icon: "book",
          color: "bg-blue-500 hover:bg-blue-600",
          action: () => getHomeworkHelp(),
          roles: ["teenager", "child"],
          priority: 3
        },
        {
          id: "schedule",
          label: "My Schedule",
          icon: "clock",
          color: "bg-orange-500 hover:bg-orange-600",
          action: () => viewPersonalSchedule(),
          roles: ["teenager"],
          priority: 4
        }
      ],
      child: [
        {
          id: "homework-help",
          label: "Homework Help",
          icon: "book",
          color: "bg-blue-500 hover:bg-blue-600",
          action: () => getHomeworkHelp(),
          roles: ["teenager", "child"],
          priority: 3
        },
        {
          id: "fun-activities",
          label: "Fun Activities",
          icon: "gamepad-2",
          color: "bg-pink-500 hover:bg-pink-600",
          action: () => showFunActivities(),
          roles: ["child"],
          priority: 4
        },
        {
          id: "stories",
          label: "Listen to Stories",
          icon: "book-open",
          color: "bg-yellow-500 hover:bg-yellow-600",
          action: () => startStoryTime(),
          roles: ["child"],
          priority: 5
        }
      ],
      grandparent: [
        {
          id: "health-reminders",
          label: "Health Reminders",
          icon: "heart",
          color: "bg-red-500 hover:bg-red-600",
          action: () => showHealthReminders(),
          roles: ["grandparent"],
          priority: 3
        },
        {
          id: "family-photos",
          label: "Family Photos",
          icon: "image",
          color: "bg-purple-500 hover:bg-purple-600",
          action: () => showFamilyPhotos(),
          roles: ["grandparent"],
          priority: 4
        },
        {
          id: "video-call",
          label: "Video Call Family",
          icon: "video",
          color: "bg-green-500 hover:bg-green-600",
          action: () => startVideoCall(),
          roles: ["grandparent"],
          priority: 5
        }
      ]
    };

    const allActions = [...baseActions, ...(roleSpecificActions[role as keyof typeof roleSpecificActions] || [])];
    return allActions
      .filter(action => action.roles.includes(role))
      .sort((a, b) => a.priority - b.priority)
      .slice(0, 6); // Limit to 6 actions for better UX
  };

  // Fetch family data
  useEffect(() => {
    const fetchFamilyData = async () => {
      try {
        // Mock data for now - replace with actual API calls
        const mockFamilyMembers: FamilyMember[] = [
          { id: "1", name: "Sarah", role: "parent", status: "work", activity: "In a meeting", location: "Office" },
          { id: "2", name: "Alex", role: "teenager", status: "school", activity: "Math class", location: "High School" },
          { id: "3", name: "Emma", role: "child", status: "school", activity: "Art class", location: "Elementary School" },
          { id: "4", name: "Robert", role: "grandparent", status: "online", activity: "Reading news", location: "Home" }
        ];

        const mockActivities: FamilyActivity[] = [
          { id: "1", type: "homework", title: "Math homework - Chapter 5", assignedTo: ["Alex"], dueTime: "3:00 PM", status: "pending" },
          { id: "2", type: "chore", title: "Clean your room", assignedTo: ["Emma"], status: "in_progress" },
          { id: "3", type: "appointment", title: "Doctor appointment", assignedTo: ["Robert"], dueTime: "5:00 PM", status: "pending" }
        ];

        setFamilyMembers(mockFamilyMembers);
        setFamilyActivities(mockActivities);
      } catch (error) {
        console.error("Failed to fetch family data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchFamilyData();
  }, []);

  // Update current time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, []);

  // Voice interaction handler
  const handleVoiceCommand = (command: string, transcript: string) => {
    setVoiceTranscript(transcript);

    // Process different types of commands
    if (command.toLowerCase().includes("calendar") || command.toLowerCase().includes("schedule")) {
      openFamilyCalendar();
    } else if (command.toLowerCase().includes("homework") || command.toLowerCase().includes("help")) {
      getHomeworkHelp();
    } else if (command.toLowerCase().includes("story") || command.toLowerCase().includes("bedtime")) {
      startStoryTime();
    } else if (command.toLowerCase().includes("family") && command.toLowerCase().includes("status")) {
      showFamilyStatus();
    } else if (command.toLowerCase().includes("where") && command.toLowerCase().includes("dad")) {
      showFamilyStatus();
    } else if (command.toLowerCase().includes("remind")) {
      openTaskManager();
    } else if (command.toLowerCase().includes("video") && command.toLowerCase().includes("call")) {
      startVideoCall();
    }

    // Clear transcript after processing
    setTimeout(() => {
      setVoiceTranscript("");
    }, 5000);
  };

  // Action handlers
  const showFamilyStatus = () => {
    console.log("Showing family status...");
  };

  const openTaskManager = () => {
    console.log("Opening task manager...");
  };

  const openParentalControls = () => {
    console.log("Opening parental controls...");
  };

  const openFamilyCalendar = () => {
    console.log("Opening family calendar...");
  };

  const getHomeworkHelp = () => {
    console.log("Getting homework help...");
  };

  const viewPersonalSchedule = () => {
    console.log("Viewing personal schedule...");
  };

  const showFunActivities = () => {
    console.log("Showing fun activities...");
  };

  const startStoryTime = () => {
    console.log("Starting story time...");
  };

  const showHealthReminders = () => {
    console.log("Showing health reminders...");
  };

  const showFamilyPhotos = () => {
    console.log("Showing family photos...");
  };

  const startVideoCall = () => {
    console.log("Starting video call...");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const userRole = user?.role || "parent";
  const quickActions = getQuickActions(userRole);
  const hour = currentTime.getHours();
  const greeting = getGreeting(userRole, hour);

  // Role-based styling
  const getRoleColors = (role: string) => {
    const colors = {
      parent: { primary: "from-blue-500 to-purple-600", secondary: "bg-blue-50 border-blue-200" },
      teenager: { primary: "from-cyan-500 to-blue-600", secondary: "bg-cyan-50 border-cyan-200" },
      child: { primary: "from-yellow-400 to-pink-500", secondary: "bg-yellow-50 border-yellow-200" },
      grandparent: { primary: "from-teal-500 to-green-600", secondary: "bg-teal-50 border-teal-200" }
    };
    return colors[role as keyof typeof colors] || colors.parent;
  };

  const roleColors = getRoleColors(userRole);

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${roleColors.primary} p-6 text-white shadow-lg`}>
        <div className="relative z-10">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">
            {greeting}
          </h1>
          <p className="text-lg opacity-90 mb-4">
            I'm {ASSISTANT_CONFIG.name}, your family coordinator. How can I help you today?
          </p>
          <div className="text-sm opacity-80">
            {currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            {" • "}
            {currentTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
          </div>
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full -mr-16 -mt-16"></div>
        <div className="absolute bottom-0 right-0 w-24 h-24 bg-white opacity-10 rounded-full -mr-12 -mb-12"></div>
      </div>

      {/* Voice Interface */}
      <div id="voice-interface">
        <VoiceInterface
          onVoiceCommand={handleVoiceCommand}
          wakeWord={ASSISTANT_CONFIG.wakeWord}
          assistantName={ASSISTANT_CONFIG.name}
        />
      </div>

      {/* Voice Command Result */}
      {voiceTranscript && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Voice Command Received:
              </p>
              <p className="text-blue-700 dark:text-blue-300">
                "{voiceTranscript}"
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions Grid */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={action.action}
              className={`${action.color} text-white rounded-xl p-4 flex flex-col items-center justify-center space-y-2 transition-all transform hover:scale-105 shadow-md hover:shadow-lg`}
            >
              {/* Icon placeholder - replace with actual icons */}
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center text-xl">
                {action.icon === 'mic' && '🎤'}
                {action.icon === 'users' && '👥'}
                {action.icon === 'checklist' && '✓'}
                {action.icon === 'shield' && '🛡️'}
                {action.icon === 'calendar' && '📅'}
                {action.icon === 'book' && '📚'}
                {action.icon === 'clock' && '🕐'}
                {action.icon === 'gamepad-2' && '🎮'}
                {action.icon === 'book-open' && '📖'}
                {action.icon === 'heart' && '❤️'}
                {action.icon === 'image' && '🖼️'}
                {action.icon === 'video' && '📹'}
              </div>
              <span className="text-xs font-medium text-center">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Family Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Family Members */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center">
            <span className="mr-2">👨‍👩‍👧‍👦</span>
            Family Members
          </h2>
          <div className="space-y-3">
            {familyMembers.map((member) => (
              <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                    {member.name[0]}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">{member.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{member.role}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      member.status === 'online' ? 'bg-green-500' :
                      member.status === 'offline' ? 'bg-gray-400' :
                      member.status === 'busy' ? 'bg-red-500' : 'bg-yellow-500'
                    }`}></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{member.status}</span>
                  </div>
                  {member.activity && (
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{member.activity}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Family Activities */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center">
            <span className="mr-2">📋</span>
            Family Activities
          </h2>
          <div className="space-y-3">
            {familyActivities.map((activity) => (
              <div key={activity.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-800 dark:text-white">{activity.title}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full capitalize">
                        {activity.type}
                      </span>
                      {activity.dueTime && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Due: {activity.dueTime}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'completed' ? 'bg-green-500' :
                    activity.status === 'in_progress' ? 'bg-yellow-500' : 'bg-gray-400'
                  } ml-2 mt-1`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}