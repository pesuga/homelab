import React from 'react';
import { MessageSquare, User, Clock, ArrowRight } from 'lucide-react';

interface Conversation {
  threadId: string;
  userId: string;
  role: string;
  content: string;
  timestamp: string;
}

interface RecentConversationsProps {
  conversations?: Conversation[];
}

export const RecentConversations: React.FC<RecentConversationsProps> = ({ conversations = [] }) => {
  // Mock data if no conversations provided
  const mockConversations: Conversation[] = [
    {
      threadId: 'thread_abc123',
      userId: 'sarah',
      role: 'user',
      content: "Can you help me with my math homework? I'm stuck on fractions.",
      timestamp: new Date(Date.now() - 10 * 60000).toISOString()
    },
    {
      threadId: 'thread_def456',
      userId: 'mike',
      role: 'assistant',
      content: "I've processed your family vacation photos. They look wonderful! Here's what I found...",
      timestamp: new Date(Date.now() - 25 * 60000).toISOString()
    },
    {
      threadId: 'thread_ghi789',
      userId: 'emma',
      role: 'user',
      content: "What's a good recipe for dinner tonight? We have chicken and vegetables.",
      timestamp: new Date(Date.now() - 45 * 60000).toISOString()
    },
    {
      threadId: 'thread_jkl012',
      userId: 'sarah',
      role: 'assistant',
      content: "For your fraction homework, remember that the denominator represents the total number of equal parts...",
      timestamp: new Date(Date.now() - 60 * 60000).toISOString()
    }
  ];

  const displayConversations = conversations.length > 0 ? conversations : mockConversations;

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

  const getUserName = (userId: string) => {
    const userNames: Record<string, string> = {
      'sarah': 'Sarah',
      'mike': 'Mike',
      'emma': 'Emma',
      'parent': 'Parent',
      'child': 'Child'
    };
    return userNames[userId] || userId;
  };

  const truncateContent = (content: string, maxLength: number = 120) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className="space-y-3">
      {displayConversations.map((conversation, index) => (
        <div
          key={`${conversation.threadId}-${index}`}
          className="group p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md hover:border-primary-300 transition-all cursor-pointer"
        >
          <div className="flex items-start gap-3">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
              conversation.role === 'user'
                ? 'bg-blue-100 text-blue-600'
                : 'bg-green-100 text-green-600'
            }`}>
              {conversation.role === 'user' ? (
                <User className="w-4 h-4" />
              ) : (
                <MessageSquare className="w-4 h-4" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-medium text-gray-900">
                  {conversation.role === 'user' ? getUserName(conversation.userId) : 'Assistant'}
                </h4>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  conversation.role === 'user'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {conversation.role}
                </span>
              </div>

              <p className="text-sm text-gray-700 mb-2 leading-relaxed">
                {truncateContent(conversation.content)}
              </p>

              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTimestamp(conversation.timestamp)}
                </p>

                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}

      {displayConversations.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">No recent conversations</p>
        </div>
      )}

      {displayConversations.length > 0 && (
        <div className="text-center pt-2">
          <button className="text-sm text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1 mx-auto">
            View all conversations
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};