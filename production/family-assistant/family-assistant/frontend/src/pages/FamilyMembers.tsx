import React, { useState } from 'react';
import { Users, Plus, Edit2, Shield, Settings, User, Mail, Calendar, ChevronDown, ChevronUp } from 'lucide-react';

interface FamilyMember {
  id: string;
  name: string;
  role: 'parent' | 'child' | 'teen' | 'guest';
  email: string;
  avatar: string;
  joinDate: string;
  lastActive: string;
  permissions: {
    chat: boolean;
    upload: boolean;
    delete: boolean;
    manage: boolean;
  };
  preferences: {
    language: string;
    theme: string;
    notifications: boolean;
  };
  stats: {
    conversations: number;
    uploads: number;
    lastMessage: string;
  };
}

interface FamilyMembersProps {}

export const FamilyMembers: React.FC<FamilyMembersProps> = () => {
  const [expandedMembers, setExpandedMembers] = useState<Set<string>>(new Set());
  const [showAddModal, setShowAddModal] = useState(false);

  // Mock family members data
  const mockMembers: FamilyMember[] = [
    {
      id: '1',
      name: 'Sarah Johnson',
      role: 'parent',
      email: 'sarah@family.local',
      avatar: 'S',
      joinDate: '2024-01-15',
      lastActive: new Date(Date.now() - 15 * 60000).toISOString(),
      permissions: {
        chat: true,
        upload: true,
        delete: true,
        manage: true
      },
      preferences: {
        language: 'English',
        theme: 'light',
        notifications: true
      },
      stats: {
        conversations: 145,
        uploads: 23,
        lastMessage: 'Can you help plan the family vacation?'
      }
    },
    {
      id: '2',
      name: 'Mike Johnson',
      role: 'parent',
      email: 'mike@family.local',
      avatar: 'M',
      joinDate: '2024-01-15',
      lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      permissions: {
        chat: true,
        upload: true,
        delete: true,
        manage: false
      },
      preferences: {
        language: 'English',
        theme: 'dark',
        notifications: true
      },
      stats: {
        conversations: 98,
        uploads: 45,
        lastMessage: 'Thanks for processing those photos!'
      }
    },
    {
      id: '3',
      name: 'Emma Johnson',
      role: 'teen',
      email: 'emma@family.local',
      avatar: 'E',
      joinDate: '2024-02-01',
      lastActive: new Date(Date.now() - 30 * 60000).toISOString(),
      permissions: {
        chat: true,
        upload: true,
        delete: false,
        manage: false
      },
      preferences: {
        language: 'English',
        theme: 'light',
        notifications: false
      },
      stats: {
        conversations: 234,
        uploads: 67,
        lastMessage: 'Can you help me with my homework?'
      }
    },
    {
      id: '4',
      name: 'Lucas Johnson',
      role: 'child',
      email: 'lucas@family.local',
      avatar: 'L',
      joinDate: '2024-03-10',
      lastActive: new Date(Date.now() - 45 * 60000).toISOString(),
      permissions: {
        chat: true,
        upload: false,
        delete: false,
        manage: false
      },
      preferences: {
        language: 'English',
        theme: 'light',
        notifications: true
      },
      stats: {
        conversations: 89,
        uploads: 12,
        lastMessage: 'Tell me a story about dragons!'
      }
    }
  ];

  const members = mockMembers; // In real app, this would be fetched from API

  const toggleExpanded = (memberId: string) => {
    const newExpanded = new Set(expandedMembers);
    if (newExpanded.has(memberId)) {
      newExpanded.delete(memberId);
    } else {
      newExpanded.add(memberId);
    }
    setExpandedMembers(newExpanded);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'parent':
        return 'bg-ctp-blue/10 text-ctp-blue';
      case 'teen':
        return 'bg-purple-100 text-purple-800';
      case 'child':
        return 'bg-ctp-green/10 text-ctp-green';
      case 'guest':
        return 'bg-ctp-surface0 text-ctp-text';
      default:
        return 'bg-ctp-surface0 text-ctp-text';
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'parent':
        return <Shield className="w-4 h-4" />;
      case 'teen':
        return <User className="w-4 h-4" />;
      case 'child':
        return <User className="w-4 h-4" />;
      case 'guest':
        return <User className="w-4 h-4" />;
      default:
        return <User className="w-4 h-4" />;
    }
  };

  const formatLastActive = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) {
      return 'Active now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const isOnline = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    return diffMs < 5 * 60 * 1000; // Active in last 5 minutes
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-ctp-text">Family Members</h1>
          <p className="text-ctp-subtext1 mt-2">
            Manage family members and their permissions
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Member
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-ctp-mantle p-4 rounded-lg border border-ctp-surface1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-ctp-blue/10 rounded-lg">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-ctp-text">{members.length}</p>
              <p className="text-sm text-ctp-subtext0">Total Members</p>
            </div>
          </div>
        </div>

        <div className="bg-ctp-mantle p-4 rounded-lg border border-ctp-surface1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-ctp-green/10 rounded-lg">
              <User className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-ctp-text">
                {members.filter(m => isOnline(m.lastActive)).length}
              </p>
              <p className="text-sm text-ctp-subtext0">Online Now</p>
            </div>
          </div>
        </div>

        <div className="bg-ctp-mantle p-4 rounded-lg border border-ctp-surface1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-50 rounded-lg">
              <Mail className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-ctp-text">
                {members.reduce((sum, m) => sum + m.stats.conversations, 0)}
              </p>
              <p className="text-sm text-ctp-subtext0">Total Conversations</p>
            </div>
          </div>
        </div>

        <div className="bg-ctp-mantle p-4 rounded-lg border border-ctp-surface1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-50 rounded-lg">
              <Settings className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-ctp-text">
                {members.filter(m => m.permissions.manage).length}
              </p>
              <p className="text-sm text-ctp-subtext0">Admins</p>
            </div>
          </div>
        </div>
      </div>

      {/* Family Members List */}
      <div className="space-y-4">
        {members.map((member) => (
          <div
            key={member.id}
            className="bg-ctp-mantle border border-ctp-surface1 rounded-lg overflow-hidden"
          >
            {/* Member Header */}
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Avatar */}
                  <div className="relative">
                    <div className="w-12 h-12 bg-primary-100 text-ctp-blue rounded-full flex items-center justify-center font-semibold">
                      {member.avatar}
                    </div>
                    {isOnline(member.lastActive) && (
                      <div className="absolute bottom-0 right-0 w-3 h-3 bg-ctp-green/100 rounded-full border-2 border-white"></div>
                    )}
                  </div>

                  {/* Member Info */}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-semibold text-ctp-text">
                        {member.name}
                      </h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(member.role)}`}>
                        {getRoleIcon(member.role)}
                        {member.role}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-ctp-subtext0">
                      <span className="flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        {member.email}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        Joined {new Date(member.joinDate).toLocaleDateString()}
                      </span>
                      <span>
                        Last active {formatLastActive(member.lastActive)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button className="p-2 text-ctp-subtext0 hover:text-ctp-blue hover:bg-ctp-blue/10 rounded-lg transition-colors">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => toggleExpanded(member.id)}
                    className="p-2 text-ctp-subtext0 hover:text-ctp-blue hover:bg-ctp-blue/10 rounded-lg transition-colors"
                  >
                    {expandedMembers.has(member.id) ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedMembers.has(member.id) && (
              <div className="border-t border-ctp-surface1 p-4 bg-ctp-surface0">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Permissions */}
                  <div>
                    <h4 className="font-medium text-ctp-text mb-3 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Permissions
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(member.permissions).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm text-ctp-subtext1 capitalize">{key}</span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            value ? 'bg-ctp-green/10 text-ctp-green' : 'bg-ctp-red/10 text-ctp-red'
                          }`}>
                            {value ? 'Allowed' : 'Denied'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preferences */}
                  <div>
                    <h4 className="font-medium text-ctp-text mb-3 flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Preferences
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-ctp-subtext1">Language</span>
                        <span className="text-sm font-medium">{member.preferences.language}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-ctp-subtext1">Theme</span>
                        <span className="text-sm font-medium capitalize">{member.preferences.theme}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-ctp-subtext1">Notifications</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          member.preferences.notifications ? 'bg-ctp-green/10 text-ctp-green' : 'bg-ctp-surface0 text-ctp-text'
                        }`}>
                          {member.preferences.notifications ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Statistics */}
                  <div>
                    <h4 className="font-medium text-ctp-text mb-3">Activity</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-ctp-subtext1">Conversations</span>
                        <span className="text-sm font-medium">{member.stats.conversations}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-ctp-subtext1">Uploads</span>
                        <span className="text-sm font-medium">{member.stats.uploads}</span>
                      </div>
                      <div className="text-sm text-ctp-subtext1">
                        <p className="font-medium mb-1">Last Message:</p>
                        <p className="text-ctp-subtext0 italic">"{member.stats.lastMessage}"</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Member Modal (placeholder) */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-ctp-mantle rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-ctp-text mb-4">Add Family Member</h2>
            <p className="text-ctp-subtext1 mb-4">
              This would open a form to add a new family member with their permissions and preferences.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-ctp-subtext1 hover:text-ctp-text transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Add Member
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};