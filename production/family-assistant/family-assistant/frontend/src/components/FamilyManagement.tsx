/**
 * Family Management Component
 *
 * Manage family members and their permissions
 */

import React from 'react';
import { useAuth } from '../auth/AuthContext';

const FamilyManagement: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Family Management</h1>
        <p className="text-gray-600 mt-1">Manage family members and their permissions</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Family Members</h2>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">👨‍👩‍👧‍👦</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Family Management</h3>
          <p className="text-gray-600 mb-4">
            This feature allows parents to manage family members, roles, and permissions.
          </p>
          <div className="text-sm text-gray-500">
            <p>Current user: {user?.first_name || user?.username} ({user?.role})</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FamilyManagement;