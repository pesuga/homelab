import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Architecture } from '@/pages/Architecture';
import { FamilyMembers } from '@/pages/FamilyMembers';
import { Settings } from '@/pages/Settings';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AlertBanner } from '@/components/AlertBanner';
import { SystemHealthProvider } from '@/contexts/SystemHealthContext';
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
  const { isConnected, lastMessage } = useWebSocket('ws://localhost:30801');

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

  return (
    <QueryClientProvider client={queryClient}>
      <SystemHealthProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
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

            {/* Main Layout */}
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/architecture" element={<Architecture />} />
                <Route path="/family" element={<FamilyMembers />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </div>
        </Router>
      </SystemHealthProvider>
    </QueryClientProvider>
  );
}

export default App;