/**
 * Family Management Component
 *
 * Manage family members and their permissions using Zustand store
 */

import React, { useEffect } from 'react';
import { useFamilyStore, FamilyMember } from '../stores/familyStore';

const FamilyManagement: React.FC = () => {
  const {
    members,
    selectedMember,
    isLoading,
    error,
    fetchMembers,
    selectMember,
    updateMember,
    deleteMember,
    clearError,
  } = useFamilyStore();

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'parent': return '👨‍👩‍👧‍👦';
      case 'teenager': return '👦';
      case 'child': return '🧒';
      case 'grandparent': return '👴👵';
      default: return '👤';
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'parent': return 'bg-purple-100 text-purple-800';
      case 'teenager': return 'bg-blue-100 text-blue-800';
      case 'child': return 'bg-green-100 text-green-800';
      case 'grandparent': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleEditMember = (member: FamilyMember) => {
    selectMember(member.id);
    // TODO: Open edit modal/form
  };

  const handleDeleteMember = async (member: FamilyMember) => {
    if (window.confirm(`Are you sure you want to remove ${member.first_name} from the family?`)) {
      try {
        await deleteMember(member.id);
      } catch (error) {
        console.error('Failed to delete member:', error);
      }
    }
  };

  const handleRetry = () => {
    clearError();
    fetchMembers();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Family Management</h1>
          <p className="text-gray-600 mt-1">Manage family members and their permissions</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Family Management</h1>
          <p className="text-gray-600 mt-1">Manage family members and their permissions</p>
        </div>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          Add Member
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <span className="text-2xl">👨‍👩‍👧‍👦</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Members</p>
              <p className="text-2xl font-bold text-gray-900">{members.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <span className="text-2xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Now</p>
              <p className="text-2xl font-bold text-gray-900">
                {members.filter(m => m.active_skills && m.active_skills.length > 0).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <span className="text-2xl">👑</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Parents</p>
              <p className="text-2xl font-bold text-gray-900">
                {members.filter(m => m.role === 'parent').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Family Members List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Family Members</h2>
        </div>

        {error ? (
          <div className="p-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <span className="text-red-400">⚠️</span>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                  <button
                    onClick={handleRetry}
                    className="mt-2 px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : members.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-6xl mb-4">👨‍👩‍👧‍👦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No family members yet</h3>
            <p className="text-gray-600 mb-4">
              Add your first family member to get started with the Family Assistant.
            </p>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
              Add First Member
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {members.map((member) => (
              <div key={member.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-4xl">
                      {getRoleIcon(member.role)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {member.first_name} {member.last_name || ''}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(member.role)}`}>
                          {member.role}
                        </span>
                        {member.active_skills && member.active_skills.length > 0 && (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {member.language_preference && `Language: ${member.language_preference}`}
                        {member.age_group && ` • Age: ${member.age_group}`}
                        {member.privacy_level && ` • Privacy: ${member.privacy_level}`}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Member since {new Date(member.created_at).toLocaleDateString()}
                        {member.updated_at && ` • Updated ${new Date(member.updated_at).toLocaleDateString()}`}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEditMember(member)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteMember(member)}
                      className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
            <h3 className="font-medium text-gray-900">📱 Send Invites</h3>
            <p className="text-sm text-gray-600 mt-1">Invite family members via email</p>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
            <h3 className="font-medium text-gray-900">🔒 Set Permissions</h3>
            <p className="text-sm text-gray-600 mt-1">Configure role-based access</p>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
            <h3 className="font-medium text-gray-900">👨‍👩‍👧‍👦 Manage Family</h3>
            <p className="text-sm text-gray-600 mt-1">Set up parental controls</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default FamilyManagement;