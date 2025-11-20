import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage as ChatMessageType } from '../types/chat';
import { sendChatMessage, getOrCreateSessionId, ChatApiError } from '../utils/chatApi';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { MessageSquare, Trash2, AlertCircle, Home } from 'lucide-react';
import toast from 'react-hot-toast';

interface ChatInterfaceProps {
  userId?: string;
  onNavigateHome?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId, onNavigateHome }) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    const id = getOrCreateSessionId();
    setSessionId(id);

    // Add welcome message
    const welcomeMessage: ChatMessageType = {
      id: 'welcome',
      content: 'Hi! I\'m your Family Assistant. How can I help you today?',
      sender: 'assistant',
      timestamp: new Date(),
      status: 'sent',
    };
    setMessages([welcomeMessage]);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (content: string) => {
    // Create user message
    const userMessage: ChatMessageType = {
      id: `user_${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date(),
      status: 'sending',
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send to API
      const response = await sendChatMessage({
        message: content,
        user_id: userId,
        session_id: sessionId,
        content_type: 'text',
      });

      // Update user message status
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id ? { ...msg, status: 'sent' } : msg
        )
      );

      // Add assistant response
      const assistantMessage: ChatMessageType = {
        id: `assistant_${Date.now()}`,
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
        status: 'sent',
        metadata: response.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Mark user message as error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id ? { ...msg, status: 'error' } : msg
        )
      );

      // Show error toast
      let errorMessage = 'Failed to send message. Please try again.';
      if (error instanceof ChatApiError) {
        errorMessage = error.message;
        if (error.details) {
          console.error('Chat API Error:', error.details);
        }
      }

      toast.error(errorMessage, {
        duration: 4000,
        icon: '⚠️',
      });

      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      setMessages([
        {
          id: 'welcome',
          content: 'Chat cleared. How can I help you?',
          sender: 'assistant',
          timestamp: new Date(),
          status: 'sent',
        },
      ]);
      toast.success('Chat history cleared');
    }
  };

  const handleRetryMessage = (messageId: string) => {
    const message = messages.find((msg) => msg.id === messageId);
    if (message && message.status === 'error') {
      // Remove the error message and resend
      setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
      handleSendMessage(message.content);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
              <MessageSquare size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Family Assistant
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Always here to help
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onNavigateHome && (
              <button
                onClick={onNavigateHome}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
                aria-label="Go to home"
              >
                <Home size={20} />
              </button>
            )}
            <button
              onClick={handleClearChat}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
              aria-label="Clear chat"
            >
              <Trash2 size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center mb-4">
              <MessageSquare size={32} className="text-white" />
            </div>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Start a conversation
            </h2>
            <p className="text-gray-500 dark:text-gray-400 max-w-md">
              Ask me anything! I can help with homework, schedule management, reminders, and more.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id}>
                <ChatMessage message={message} showTimestamp />
                {message.status === 'error' && (
                  <div className="flex justify-end mb-4">
                    <button
                      onClick={() => handleRetryMessage(message.id)}
                      className="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 flex items-center gap-1"
                    >
                      <AlertCircle size={12} />
                      Retry
                    </button>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder={
            isLoading
              ? 'Waiting for response...'
              : 'Type your message...'
          }
        />
      </div>
    </div>
  );
};

export default ChatInterface;
