"use client";

import React, { useState, useEffect } from "react";
import { useFamilyData } from "@/hooks/useFamilyData";
import { FamilyMember, ParentalControls } from "@/lib/api-client";

export default function MyFamily() {
  const [activeTab, setActiveTab] = useState("members");
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const {
    members,
    membersLoading,
    membersError,
    createMember,
    updateMember,
    deleteMember,
    controls,
    controlsLoading,
    controlsError,
    fetchControls,
    updateControls,
    reports,
    reportsLoading,
    reportsError,
    fetchReports,
  } = useFamilyData();

  // Fetch controls for children when switching to controls tab
  useEffect(() => {
    if (activeTab === "controls") {
      members
        .filter((m) => m.role === "child" || m.role === "teenager")
        .forEach((m) => fetchControls(m.id));
    }
  }, [activeTab, members, fetchControls]);

  // Fetch reports when switching to reports tab
  useEffect(() => {
    if (activeTab === "reports") {
      fetchReports();
    }
  }, [activeTab, fetchReports]);

  // Mock feature flags (backend endpoint not yet implemented)
  const featureFlags = [
    { id: "voice_assistant", name: "Voice Assistant", enabled: true, scope: "all" },
    { id: "ai_homework_help", name: "AI Homework Help", enabled: true, scope: "teenagers" },
    { id: "screen_time_reports", name: "Screen Time Reports", enabled: true, scope: "parents" },
    { id: "family_chat", name: "Family Chat", enabled: true, scope: "all" },
    { id: "content_recommendations", name: "Content Recommendations", enabled: false, scope: "all" },
  ];

  const tabs = [
    { id: "members", name: "Family Members", icon: "👥" },
    { id: "controls", name: "Parental Controls", icon: "🛡️" },
    { id: "features", name: "Feature Flags", icon: "🚩" },
    { id: "reports", name: "Activity Reports", icon: "📊" },
  ];

  const handleDeleteMember = async (id: string) => {
    if (confirm("Are you sure you want to delete this family member?")) {
      try {
        await deleteMember(id);
      } catch (error) {
        console.error("Failed to delete member:", error);
      }
    }
  };

  const handleUpdateControls = async (memberId: string, newControls: ParentalControls) => {
    try {
      await updateControls(memberId, newControls);
      alert("Parental controls updated successfully!");
    } catch (error) {
      console.error("Failed to update controls:", error);
      alert("Failed to update controls. Please try again.");
    }
  };

  // Helper to get emoji avatar based on role
  const getAvatarEmoji = (role: string) => {
    switch (role) {
      case "parent":
        return "👨";
      case "teenager":
        return "👧";
      case "child":
        return "👦";
      case "grandparent":
        return "👴";
      default:
        return "👤";
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-gray-800 dark:text-white">
          MyFamily
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          Manage family members, settings, and controls
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </div>

      {/* Error Messages */}
      {membersError && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {membersError}
        </div>
      )}
      {controlsError && activeTab === "controls" && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {controlsError}
        </div>
      )}
      {reportsError && activeTab === "reports" && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-800 dark:text-red-400 rounded">
          {reportsError}
        </div>
      )}

      {/* Family Members Tab */}
      {activeTab === "members" && (
        <div className="space-y-4">
          {membersLoading ? (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading family members...</p>
            </div>
          ) : members.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                No family members found. Add your first family member to get started.
              </p>
            </div>
          ) : (
            members.map((member) => (
              <div
                key={member.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-5xl">{member.avatar || getAvatarEmoji(member.role)}</div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                        {member.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {member.email} • {member.role}
                      </p>
                      {member.last_active && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          Last active: {new Date(member.last_active).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingMember(member)}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteMember(member.id)}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Language: {member.language_preference === "en" ? "English" : "Spanish"}
                  </p>
                </div>
              </div>
            ))
          )}
          <button
            onClick={() => setShowAddForm(true)}
            className="w-full md:w-auto px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            + Add Family Member
          </button>
        </div>
      )}

      {/* Parental Controls Tab */}
      {activeTab === "controls" && (
        <div className="space-y-6">
          {controlsLoading ? (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading parental controls...</p>
            </div>
          ) : (
            members
              .filter((m) => m.role === "child" || m.role === "teenager")
              .map((member) => {
                const memberControls = controls[member.id];
                if (!memberControls) {
                  return (
                    <div
                      key={member.id}
                      className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
                    >
                      <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
                        Controls for {member.name}
                      </h3>
                      <p className="text-gray-500 dark:text-gray-400">
                        No parental controls configured. Click "Setup Controls" to begin.
                      </p>
                      <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                        Setup Controls
                      </button>
                    </div>
                  );
                }

                return (
                  <div
                    key={member.id}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
                  >
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
                      Controls for {member.name}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Safe Search
                        </label>
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={memberControls.safe_search}
                            onChange={(e) =>
                              handleUpdateControls(member.id, {
                                ...memberControls,
                                safe_search: e.target.checked,
                              })
                            }
                            className="mr-2 h-5 w-5"
                          />
                          <span className="text-gray-600 dark:text-gray-400">
                            {memberControls.safe_search ? "Enabled" : "Disabled"}
                          </span>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Content Filter
                        </label>
                        <select
                          value={memberControls.content_filter}
                          onChange={(e) =>
                            handleUpdateControls(member.id, {
                              ...memberControls,
                              content_filter: e.target.value as "strict" | "moderate" | "off",
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                        >
                          <option value="strict">Strict</option>
                          <option value="moderate">Moderate</option>
                          <option value="off">Off</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Daily Screen Time (hours)
                        </label>
                        <input
                          type="number"
                          value={memberControls.screen_time_daily}
                          onChange={(e) =>
                            handleUpdateControls(member.id, {
                              ...memberControls,
                              screen_time_daily: parseInt(e.target.value),
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Weekend Screen Time (hours)
                        </label>
                        <input
                          type="number"
                          value={memberControls.screen_time_weekend}
                          onChange={(e) =>
                            handleUpdateControls(member.id, {
                              ...memberControls,
                              screen_time_weekend: parseInt(e.target.value),
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Allowed Apps
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {memberControls.allowed_apps.map((app) => (
                            <span
                              key={app}
                              className="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400 text-xs rounded"
                            >
                              {app}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Blocked Keywords
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {memberControls.blocked_keywords.map((keyword) => (
                            <span
                              key={keyword}
                              className="px-2 py-1 bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-400 text-xs rounded"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
          )}
          {members.filter((m) => m.role === "child" || m.role === "teenager").length === 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                No children or teenagers in the family. Add family members first.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Feature Flags Tab */}
      {activeTab === "features" && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
              Family Features
            </h3>
            <div className="mb-4 p-4 bg-yellow-100 dark:bg-yellow-900/20 border border-yellow-400 dark:border-yellow-800 text-yellow-800 dark:text-yellow-400 rounded">
              ⚠️ Feature flags are currently using mock data. Backend endpoint not yet implemented.
            </div>
            <div className="space-y-4">
              {featureFlags.map((feature) => (
                <div
                  key={feature.id}
                  className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-0"
                >
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">
                      {feature.name}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Scope: {feature.scope}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={feature.enabled}
                      className="sr-only peer"
                      readOnly
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Activity Reports Tab */}
      {activeTab === "reports" && (
        <div className="space-y-6">
          {reportsLoading ? (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading activity reports...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                No activity reports available yet. Reports will appear here once family members start using the system.
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total Queries Today</p>
                  <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                    {reports.reduce((sum, r) => sum + r.queries, 0)}
                  </p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Avg Screen Time</p>
                  <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                    {(
                      reports.reduce((sum, r) => sum + r.screen_time_hours, 0) / reports.length
                    ).toFixed(1)}
                    h
                  </p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Active Members</p>
                  <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">
                    {reports.length}/{members.length}
                  </p>
                </div>
              </div>

              {reports.map((report, idx) => (
                <div
                  key={idx}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                      {report.user_name}
                    </h3>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {report.date}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Queries</p>
                      <p className="text-2xl font-bold text-gray-800 dark:text-white">
                        {report.queries}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Screen Time</p>
                      <p className="text-2xl font-bold text-gray-800 dark:text-white">
                        {report.screen_time_hours}h
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Topics</p>
                      <div className="flex flex-wrap gap-2">
                        {report.topics.map((topic) => (
                          <span
                            key={topic}
                            className="px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400 text-xs rounded"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              <button className="w-full md:w-auto px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Download Full Report
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
