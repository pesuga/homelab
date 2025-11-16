import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Architecture } from './pages/Architecture';
import { FamilyMembers } from './pages/FamilyMembers';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useWebSocket } from './hooks/useWebSocket';
import { AlertBanner } from './components/AlertBanner';
import { SystemHealthProvider } from './contexts/SystemHealthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WS_URL } from './utils/api';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 10000,
    },
  },
});

function App() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const { isAuthenticated, isLoading } = useAuth();
  const { isConnected, lastMessage } = useWebSocket(WS_URL);

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);
        if (data.type === 'alert') {
          setAlerts(prev => [data.data, ...prev.slice(0, 4)]); // Keep only 5 most recent
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Handle authentication loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <SystemHealthProvider>
            <Router>
              <div className="min-h-screen bg-ctp-base">
                {/* Connection Status Indicator */}
                <div className="fixed top-4 right-4 z-50">
                  <div className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg ${
                    isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} ${isConnected ? '' : 'pulse-animation'}`} />
                    <span className="text-sm font-medium">
                      {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>

                {/* Alert Banner */}
                {alerts.length > 0 && <AlertBanner alerts={alerts} onDismiss={(id) => setAlerts(prev => prev.filter(alert => alert.id !== id))} />}

                {/* Routes */}
                <Routes>
                  {/* Public Route - Login */}
                  <Route
                    path="/login"
                    element={
                      isAuthenticated ? <Navigate to="/" replace /> : <Login />
                    }
                  />

                  {/* Protected Routes */}
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <Dashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/architecture"
                    element={
                      <ProtectedRoute>
                        <Architecture />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/family"
                    element={
                      <ProtectedRoute>
                        <FamilyMembers />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/settings"
                    element={
                      <ProtectedRoute>
                        <Settings />
                      </ProtectedRoute>
                    }
                  />

                  {/* Catch-all - Redirect to login if not authenticated */}
                  <Route
                    path="*"
                    element={
                      isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/login" replace />
                    }
                  />
                </Routes>
              </div>
            </Router>
          </SystemHealthProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;