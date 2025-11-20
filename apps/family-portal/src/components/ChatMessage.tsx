import React from 'react';
import { ChatMessage as ChatMessageType } from '../types/chat';
import { User, Bot, Clock, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

interface ChatMessageProps {
  message: ChatMessageType;
  showTimestamp?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, showTimestamp = true }) => {
  const isUser = message.sender === 'user';
  const isError = message.status === 'error';
  const isSending = message.status === 'sending';

  return (
    <div
      className={`flex items-start gap-3 mb-4 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-amber-500 text-white'
            : 'bg-blue-500 text-white'
        }`}
      >
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? 'bg-amber-500 text-white rounded-tr-sm'
              : isError
              ? 'bg-red-100 text-red-900 dark:bg-red-900 dark:text-red-100 rounded-tl-sm border border-red-300 dark:border-red-700'
              : 'bg-white text-gray-800 dark:bg-gray-700 dark:text-gray-100 rounded-tl-sm border border-gray-200 dark:border-gray-600'
          } ${isSending ? 'opacity-60' : 'opacity-100'}`}
        >
          {isError && (
            <div className="flex items-center gap-2 mb-2 text-red-600 dark:text-red-400">
              <AlertCircle size={16} />
              <span className="text-xs font-semibold">Failed to send</span>
            </div>
          )}
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
        </div>

        {/* Timestamp */}
        {showTimestamp && (
          <div className={`flex items-center gap-1 mt-1 px-2 ${
            isUser ? 'flex-row-reverse' : 'flex-row'
          }`}>
            <Clock size={12} className="text-gray-400 dark:text-gray-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {format(message.timestamp, 'HH:mm')}
            </span>
            {isSending && (
              <span className="text-xs text-gray-400 dark:text-gray-500 ml-1">
                Sending...
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
