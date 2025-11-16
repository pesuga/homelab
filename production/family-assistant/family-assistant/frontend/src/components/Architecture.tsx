/**
 * Architecture Component
 *
 * System architecture documentation and overview
 */

import React from 'react';
import { useAuth } from '../auth/AuthContext';

const Architecture: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Architecture</h1>
        <p className="text-gray-600 mt-1">System documentation and architecture overview</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Architecture</h2>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏗️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Architecture Documentation</h3>
          <p className="text-gray-600 mb-4">
            Comprehensive documentation of the Family Assistant platform architecture,
            including deployment patterns, service interactions, and technology stack.
          </p>
          <div className="text-sm text-gray-500">
            <p>View detailed system diagrams and technical specifications</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Architecture;