import { React, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Server,
  Users,
  Settings,
  Menu,
  X,
  Activity
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: Home,
      current: location.pathname === '/',
    },
    {
      name: 'Architecture',
      href: '/architecture',
      icon: Server,
      current: location.pathname === '/architecture',
    },
    {
      name: 'Family Members',
      href: '/family',
      icon: Users,
      current: location.pathname === '/family',
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      current: location.pathname === '/settings',
    },
  ];

  return (
    <div className="flex h-screen bg-ctp-base">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden bg-ctp-crust bg-opacity-75"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-ctp-mantle shadow-lg transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-ctp-surface0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-ctp-blue to-ctp-mauve rounded-lg flex items-center justify-center">
              <Home className="w-5 h-5 text-ctp-base" />
            </div>
            <h1 className="text-xl font-bold text-ctp-text">Family Assistant</h1>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-ctp-subtext0 hover:text-ctp-text"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="mt-6 px-3">
          <div className="space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`sidebar-item ${item.current ? 'active' : ''}`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            ))}
          </div>
        </nav>

        {/* System Status */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-ctp-surface0">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-ctp-subtext1">
              <Activity className="w-4 h-4" />
              <span>System Status</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-ctp-green rounded-full" />
                <span className="text-xs text-ctp-subtext0">API</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-ctp-green rounded-full" />
                <span className="text-xs text-ctp-subtext0">DB</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-ctp-green rounded-full" />
                <span className="text-xs text-ctp-subtext0">AI</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-ctp-mantle shadow-sm border-b border-ctp-surface0">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-ctp-subtext0 hover:text-ctp-text"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1"></div>

            {/* Theme Toggle */}
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};