import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FamilyMember, FamilyActivity } from '../types/family';
import { getAdaptiveConfig, getTimeOfDay } from '../utils/adaptiveConfig';
import { useTheme } from '../context/ThemeContext';
import ThemeToggle from './ThemeToggle';
import {
  Users,
  Calendar,
  Bell,
  BookOpen,
  Gamepad2,
  Music,
  MessageCircle,
  Play,
  Image,
  Video,
  Mic,
  MicOff,
  Volume2,
  Sun,
  Cloud,
  Moon
} from 'lucide-react';

interface AdaptiveHomeScreenProps {
  currentUser: FamilyMember;
  familyMembers: FamilyMember[];
  familyActivities: FamilyActivity[];
  onVoiceInteraction: (command: string) => void;
}

const AdaptiveHomeScreen: React.FC<AdaptiveHomeScreenProps> = ({
  currentUser,
  familyMembers,
  familyActivities,
  onVoiceInteraction
}) => {
  const navigate = useNavigate();
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [timeOfDay, setTimeOfDay] = useState<'morning' | 'afternoon' | 'evening'>(getTimeOfDay());
  const { isDark } = useTheme();

  const config = getAdaptiveConfig(currentUser.role);
  const onlineMembers = familyMembers.filter(m => m.isOnline);
  const myActivities = familyActivities.filter(a => a.memberId === currentUser.id && a.status === 'active');

  useEffect(() => {
    // Update time of day
    const interval = setInterval(() => {
      setTimeOfDay(getTimeOfDay());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const getTimeIcon = () => {
    switch (timeOfDay) {
      case 'morning': return <Sun className="w-5 h-5" />;
      case 'afternoon': return <Cloud className="w-5 h-5" />;
      case 'evening': return <Moon className="w-5 h-5" />;
    }
  };

  const getGreeting = () => {
    const greetings = config.greeting[timeOfDay];
    return greetings[Math.floor(Math.random() * greetings.length)];
  };

  const getDensityClasses = () => {
    switch (config.layoutDensity) {
      case 'spacious': return 'layout-spacious';
      case 'compact': return 'layout-compact';
      default: return 'layout-comfortable';
    }
  };

  const getTextSizeClasses = () => {
    switch (config.fontSize) {
      case 'extra-large': return 'text-scale-grandparent';
      case 'large': return 'text-scale-child';
      case 'small': return 'text-scale-teen';
      default: return 'text-scale-parent';
    }
  };

  const getQuickActionIcon = (iconName: string) => {
    const icons = {
      'users': Users,
      'calendar': Calendar,
      'bell': Bell,
      'book-open': BookOpen,
      'gamepad-2': Gamepad2,
      'music': Music,
      'message-circle': MessageCircle,
      'play': Play,
      'image': Image,
      'video': Video,
      'book': BookOpen,
      'pencil': BookOpen,
    };
    const Icon = icons[iconName as keyof typeof icons] || BookOpen;
    return <Icon className={`w-6 h-6 ${currentUser.role === 'grandparent' ? 'w-8 h-8' : ''}`} />;
  };

  const handleVoiceCommand = () => {
    if (isListening) {
      setIsListening(false);
      // Process the transcript
      if (currentTranscript.trim()) {
        onVoiceInteraction(currentTranscript);
        setCurrentTranscript('');
      }
    } else {
      setIsListening(true);
      // Simulate voice recognition
      setTimeout(() => {
        setCurrentTranscript("What's on the family schedule today?");
        setIsListening(false);
      }, 2000);
    }
  };

  const getColorSchemeClasses = () => {
    if (isDark) {
      return 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900';
    }

    switch (config.colorScheme) {
      case 'playful':
        return 'bg-gradient-to-br from-yellow-50 via-orange-50 to-pink-50';
      case 'calm':
        return 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50';
      case 'accessible':
        return 'bg-gradient-to-br from-gray-50 to-gray-100';
      default:
        return 'bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50';
    }
  };

  return (
    <div className={`min-h-screen ${getColorSchemeClasses()} ${getDensityClasses()} transition-all duration-300`}>
      <div className="max-w-6xl mx-auto p-4 md:p-6">
        {/* Header with Greeting */}
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {getTimeIcon()}
              <h1 className={`${getTextSizeClasses()} font-bold ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>
                {getGreeting()}, {currentUser.name}!
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {getTimeIcon()}
                <span className="text-sm md:text-base">
                  {timeOfDay === 'morning' ? 'Morning' : timeOfDay === 'afternoon' ? 'Afternoon' : 'Evening'}
                </span>
              </div>
              <ThemeToggle />
            </div>
          </div>

          {/* Family Status Bar */}
          <div className={`${isDark ? 'bg-gray-800/80 border-gray-700' : 'bg-white/80 border-white/20'} backdrop-blur-sm rounded-2xl p-4 shadow-lg border`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-green-500" />
                <span className={`${getTextSizeClasses()} font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>
                  Family Online
                </span>
              </div>
              <div className="flex -space-x-2">
                {onlineMembers.map((member) => (
                  <div
                    key={member.id}
                    className={`w-8 h-8 md:w-10 md:h-10 rounded-full border-2 ${isDark ? 'border-gray-800' : 'border-white'} flex items-center justify-center text-white font-medium
                      ${member.role === 'parent' ? 'bg-purple-500' : ''}
                      ${member.role === 'teenager' ? 'bg-blue-500' : ''}
                      ${member.role === 'child' ? 'bg-yellow-500' : ''}
                      ${member.role === 'grandparent' ? 'bg-teal-500' : ''}
                    `}
                    title={member.name}
                  >
                    {member.name.charAt(0).toUpperCase()}
                  </div>
                ))}
                {onlineMembers.length === 0 && (
                  <span className={`${isDark ? 'text-gray-400' : 'text-gray-500'} text-sm`}>No one else is online</span>
                )}
              </div>
            </div>

            {/* Current Activities */}
            {myActivities.length > 0 && (
              <div className={`mt-3 pt-3 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                <p className={`text-sm mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Currently doing:</p>
                <div className="flex flex-wrap gap-2">
                  {myActivities.map((activity) => (
                    <span
                      key={activity.id}
                      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                        isDark ? 'bg-blue-900/50 text-blue-300' : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {activity.title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Voice Interaction Area */}
        <section className="mb-8">
          <div className={`${isDark ? 'bg-gray-800/90 border-gray-700' : 'bg-white/90 border-white/20'} backdrop-blur-sm rounded-2xl p-6 shadow-lg border`}>
            <div className="text-center">
              <h2 className={`${getTextSizeClasses()} font-semibold ${isDark ? 'text-gray-100' : 'text-gray-800'} mb-4`}>
                What can I help you with?
              </h2>

              {/* Voice Button */}
              <button
                onClick={handleVoiceCommand}
                className={`mx-auto mb-4 w-16 h-16 md:w-20 md:h-20 rounded-full flex items-center justify-center transition-all duration-200
                  ${isListening
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                    : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 hover:scale-105'
                  } text-white shadow-lg`}
                aria-label={isListening ? "Stop listening" : "Start voice command"}
              >
                {isListening ? (
                  <MicOff className="w-8 h-8" />
                ) : (
                  <Mic className="w-8 h-8" />
                )}
              </button>

              {/* Transcription Display */}
              {currentTranscript && (
                <div className={`mb-4 p-3 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-100'}`}>
                  <p className={`${getTextSizeClasses()} ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>"{currentTranscript}"</p>
                </div>
              )}

              {/* Visual Feedback */}
              {isListening && (
                <div className={`flex items-center justify-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Volume2 className="w-4 h-4 animate-pulse" />
                  <span className="text-sm">Listening...</span>
                </div>
              )}

              {/* Example Commands */}
              <div className="text-left mt-6">
                <p className={`text-sm mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Try saying:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <Mic className={`w-4 h-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>"Help me with my homework"</span>
                  </div>
                  <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <Mic className={`w-4 h-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>"What's on the schedule today?"</span>
                  </div>
                  <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <Mic className={`w-4 h-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>"Tell me a story"</span>
                  </div>
                  <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <Mic className={`w-4 h-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>"Set a reminder for..."</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Actions Grid */}
        <section className="mb-8">
          <h2 className={`${getTextSizeClasses()} font-semibold ${isDark ? 'text-gray-100' : 'text-gray-800'} mb-4`}>
            Quick Actions
          </h2>
          <div className={`grid gap-4 ${
            currentUser.role === 'grandparent' ? 'grid-cols-2' :
            currentUser.role === 'child' ? 'grid-cols-2 md:grid-cols-4' :
            'grid-cols-2 md:grid-cols-4'
          }`}>
            {/* Chat Action - Always First */}
            <button
              onClick={() => navigate('/chat')}
              className={`${
                isDark
                  ? 'bg-gray-800/90 border-gray-700 hover:bg-gray-700/90'
                  : 'bg-white/90 border-white/20 hover:bg-white/100'
              } backdrop-blur-sm rounded-xl p-4 md:p-6 shadow-lg border
                hover:shadow-xl hover:scale-105 transition-all duration-200 text-center
                ${currentUser.role === 'child' ? 'hover:animate-bounce-gentle' : ''}
              `}
            >
              <div className={`mx-auto mb-2 ${
                currentUser.role === 'grandparent' ? 'w-12 h-12' : 'w-10 h-10'
              } flex items-center justify-center rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white`}>
                <MessageCircle className={`w-6 h-6 ${currentUser.role === 'grandparent' ? 'w-8 h-8' : ''}`} />
              </div>
              <span className={`${getTextSizeClasses()} font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>
                Chat {currentUser.role === 'child' ? '💬' : ''}
              </span>
            </button>

            {/* Other Quick Actions */}
            {config.quickActions.slice(0, currentUser.role === 'grandparent' ? 3 : 7).map((action) => (
              <button
                key={action.id}
                onClick={action.action}
                className={`${
                  isDark
                    ? 'bg-gray-800/90 border-gray-700 hover:bg-gray-700/90'
                    : 'bg-white/90 border-white/20 hover:bg-white/100'
                } backdrop-blur-sm rounded-xl p-4 md:p-6 shadow-lg border
                  hover:shadow-xl hover:scale-105 transition-all duration-200 text-center
                  ${currentUser.role === 'child' ? 'hover:animate-bounce-gentle' : ''}
                `}
              >
                <div className={`mx-auto mb-2 ${
                  currentUser.role === 'grandparent' ? 'w-12 h-12' : 'w-10 h-10'
                } flex items-center justify-center rounded-lg bg-gradient-to-r ${
                  action.category === 'homework' ? 'from-blue-400 to-blue-600' :
                  action.category === 'entertainment' ? 'from-purple-400 to-pink-400' :
                  action.category === 'family' ? 'from-green-400 to-teal-400' :
                  action.category === 'schedule' ? 'from-orange-400 to-yellow-400' :
                  'from-gray-400 to-gray-600'
                } text-white`}>
                  {getQuickActionIcon(action.icon)}
                </div>
                <span className={`${getTextSizeClasses()} font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>
                  {action.label}
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* Family Activity Preview (Parent View) */}
        {currentUser.role === 'parent' && (
          <section className="mb-8">
            <h2 className={`${getTextSizeClasses()} font-semibold ${isDark ? 'text-gray-100' : 'text-gray-800'} mb-4`}>
              Family Activity
            </h2>
            <div className={`${isDark ? 'bg-gray-800/90 border-gray-700' : 'bg-white/90 border-white/20'} backdrop-blur-sm rounded-2xl p-6 shadow-lg border`}>
              <div className="grid gap-4 md:grid-cols-2">
                {/* Recent Activities */}
                <div>
                  <h3 className={`font-medium mb-3 ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>Recent Activities</h3>
                  <div className="space-y-2">
                    {familyActivities.slice(0, 3).map((activity) => {
                      const member = familyMembers.find(m => m.id === activity.memberId);
                      return (
                        <div key={activity.id} className={`flex items-center gap-3 p-2 rounded-lg ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium
                            ${member?.role === 'parent' ? 'bg-purple-500' : ''}
                            ${member?.role === 'teenager' ? 'bg-blue-500' : ''}
                            ${member?.role === 'child' ? 'bg-yellow-500' : ''}
                            ${member?.role === 'grandparent' ? 'bg-teal-500' : ''}
                          `}>
                            {member?.name.charAt(0).toUpperCase()}
                          </div>
                          <div className="flex-1">
                            <p className={`text-sm font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>{activity.title}</p>
                            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{member?.name}</p>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            activity.status === 'active' ? (isDark ? 'bg-green-900/50 text-green-300' : 'bg-green-100 text-green-700') :
                            activity.status === 'completed' ? (isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700') :
                            (isDark ? 'bg-yellow-900/50 text-yellow-300' : 'bg-yellow-100 text-yellow-700')
                          }`}>
                            {activity.status}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Quick Family Stats */}
                <div>
                  <h3 className={`font-medium mb-3 ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>Family Overview</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-blue-900/30' : 'bg-blue-50'}`}>
                      <div className={`text-2xl font-bold ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>{onlineMembers.length}</div>
                      <div className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>Online Now</div>
                    </div>
                    <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-green-900/30' : 'bg-green-50'}`}>
                      <div className={`text-2xl font-bold ${isDark ? 'text-green-400' : 'text-green-600'}`}>{myActivities.length}</div>
                      <div className={`text-sm ${isDark ? 'text-green-300' : 'text-green-700'}`}>Active Tasks</div>
                    </div>
                    <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-purple-900/30' : 'bg-purple-50'}`}>
                      <div className={`text-2xl font-bold ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>5</div>
                      <div className={`text-sm ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>Reminders Today</div>
                    </div>
                    <div className={`p-3 rounded-lg text-center ${isDark ? 'bg-orange-900/30' : 'bg-orange-50'}`}>
                      <div className={`text-2xl font-bold ${isDark ? 'text-orange-400' : 'text-orange-600'}`}>3</div>
                      <div className={`text-sm ${isDark ? 'text-orange-300' : 'text-orange-700'}`}>Events Today</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default AdaptiveHomeScreen;