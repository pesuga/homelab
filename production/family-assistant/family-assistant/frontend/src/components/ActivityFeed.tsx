import React from 'react';
import { MessageCircle, Upload, Users, Activity, Clock } from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'conversation' | 'upload' | 'user_join' | 'system';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
}

interface ActivityFeedProps {
  activities?: ActivityItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities = [] }) => {
  // Mock data if no activities provided
  const mockActivities: ActivityItem[] = [
    {
      id: '1',
      type: 'conversation',
      title: 'New conversation started',
      description: 'Family member asked about homework help',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      user: 'Sarah'
    },
    {
      id: '2',
      type: 'upload',
      title: 'Photo uploaded',
      description: 'Family vacation photo processed',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      user: 'Mike'
    },
    {
      id: '3',
      type: 'system',
      title: 'System update',
      description: 'Memory optimization completed',
      timestamp: new Date(Date.now() - 30 * 60000).toISOString()
    },
    {
      id: '4',
      type: 'conversation',
      title: 'Recipe discussion',
      description: 'Meal planning conversation',
      timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
      user: 'Emma'
    }
  ];

  const displayActivities = activities.length > 0 ? activities : mockActivities;

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'conversation':
        return <MessageCircle className="w-4 h-4 text-blue-500" />;
      case 'upload':
        return <Upload className="w-4 h-4 text-green-500" />;
      case 'user_join':
        return <Users className="w-4 h-4 text-purple-500" />;
      case 'system':
        return <Activity className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="space-y-3">
      {displayActivities.map((activity) => (
        <div
          key={activity.id}
          className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex-shrink-0 mt-0.5">
            {getActivityIcon(activity.type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {activity.title}
              </h4>
              {activity.user && (
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {activity.user}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 mb-1">{activity.description}</p>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimestamp(activity.timestamp)}
            </p>
          </div>
        </div>
      ))}

      {displayActivities.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">No recent activity</p>
        </div>
      )}
    </div>
  );
};