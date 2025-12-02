import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { FamilyMember, FamilyActivity } from './types/family';
import AdaptiveHomeScreen from './components/AdaptiveHomeScreen';
import ChatInterface from './components/ChatInterface';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import { Toaster } from 'react-hot-toast';

// Mock data for development
const mockCurrentUser: FamilyMember = {
  id: '1',
  name: 'Sarah',
  role: 'parent',
  age: 35,
  isOnline: true,
  currentActivity: 'Managing family schedule',
  preferences: {
    language: 'en',
    voiceGender: 'female',
    theme: 'light',
    textSize: 'medium'
  }
};

const mockFamilyMembers: FamilyMember[] = [
  mockCurrentUser,
  {
    id: '2',
    name: 'Alex',
    role: 'teenager',
    age: 16,
    isOnline: true,
    currentActivity: 'Doing homework',
    preferences: {
      language: 'en',
      voiceGender: 'male',
      theme: 'dark',
      textSize: 'small'
    }
  },
  {
    id: '3',
    name: 'Emma',
    role: 'child',
    age: 10,
    isOnline: false,
    currentActivity: 'Playing outside',
    preferences: {
      language: 'en',
      voiceGender: 'female',
      theme: 'light',
      textSize: 'large'
    }
  },
  {
    id: '4',
    name: 'Grandpa Robert',
    role: 'grandparent',
    age: 72,
    isOnline: true,
    currentActivity: 'Reading the news',
    preferences: {
      language: 'en',
      voiceGender: 'male',
      theme: 'light',
      textSize: 'extra-large'
    }
  }
];

const mockActivities: FamilyActivity[] = [
  {
    id: '1',
    memberId: '1',
    type: 'family',
    title: 'Planning family dinner',
    description: 'Deciding on tonight\'s family dinner menu',
    startTime: new Date(Date.now() - 30 * 60 * 1000),
    status: 'active'
  },
  {
    id: '2',
    memberId: '2',
    type: 'homework',
    title: 'Math homework',
    description: 'Algebra equations and geometry problems',
    startTime: new Date(Date.now() - 60 * 60 * 1000),
    endTime: new Date(Date.now() + 30 * 60 * 1000),
    status: 'active'
  },
  {
    id: '3',
    memberId: '3',
    type: 'entertainment',
    title: 'Playing games',
    description: 'Educational games on tablet',
    startTime: new Date(Date.now() - 45 * 60 * 1000),
    status: 'completed'
  }
];

// Home component wrapper to use navigate
const HomeScreen: React.FC<{
  currentUser: FamilyMember;
  familyMembers: FamilyMember[];
  familyActivities: FamilyActivity[];
  onVoiceInteraction: (command: string) => void;
}> = ({ currentUser, familyMembers, familyActivities, onVoiceInteraction }) => {
  return (
    <AdaptiveHomeScreen
      currentUser={currentUser}
      familyMembers={familyMembers}
      familyActivities={familyActivities}
      onVoiceInteraction={onVoiceInteraction}
    />
  );
};

// Chat page wrapper to use navigate
const ChatPage: React.FC<{ currentUser: FamilyMember }> = ({ currentUser }) => {
  const navigate = useNavigate();
  return (
    <ChatInterface
      userId={currentUser.id}
      onNavigateHome={() => navigate('/')}
    />
  );
};

const App: React.FC = () => {
  const [currentUser] = useState<FamilyMember>(mockCurrentUser);
  const [familyMembers] = useState<FamilyMember[]>(mockFamilyMembers);
  const [familyActivities] = useState<FamilyActivity[]>(mockActivities);

  const handleVoiceInteraction = (command: string) => {
    console.log('Voice command received:', command);
    // TODO: Process voice command through backend
  };

  return (
    <ThemeProvider currentUser={currentUser}>
      <Router>
        <AuthProvider>
          <div className="App min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-300">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/auth/callback" element={<AuthCallback />} />

              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <HomeScreen
                      currentUser={currentUser}
                      familyMembers={familyMembers}
                      familyActivities={familyActivities}
                      onVoiceInteraction={handleVoiceInteraction}
                    />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <ChatPage currentUser={currentUser} />
                  </ProtectedRoute>
                }
              />
            </Routes>
            <Toaster
              position="top-center"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#fff',
                  color: '#374151',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                  borderRadius: '12px',
                  border: '1px solid #e5e7eb',
                },
                className: 'dark:!bg-gray-800 dark:!text-gray-100 dark:!border-gray-700',
              }}
            />
          </div>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
};

export default App;