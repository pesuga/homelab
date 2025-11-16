/**
 * Settings Component
 *
 * System settings and configuration
 */

import React from 'react';
import { useAuth } from '../auth/AuthContext';

const Settings: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure your Family Assistant system</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Configuration</h2>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">⚙️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Settings Panel</h3>
          <p className="text-gray-600 mb-4">
            This area allows administrators to configure system settings, security preferences,
            and AI behavior parameters.
          </p>
          <div className="text-sm text-gray-500">
            <p>Admin access required for configuration changes</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;