import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Bell,
  Shield,
  Database,
  Monitor,
  HelpCircle,
  Save,
  RotateCcw,
  Download,
  Upload,
  AlertTriangle,
  Check,
  X,
  Info,
  Zap,
  Lock,
  Globe
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

interface SettingsProps {}

interface SettingsSection {
  id: string;
  title: string;
  icon: React.ElementType;
  description: string;
  settings: {
    key: string;
    label: string;
    type: 'toggle' | 'select' | 'number' | 'text';
    value: any;
    options?: string[];
    description?: string;
  }[];
}

export const Settings: React.FC<SettingsProps> = () => {
  const { flavor, setFlavor } = useTheme();
  const [activeSection, setActiveSection] = useState('general');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Mock settings data
  const [settingsData, setSettingsData] = useState({
    general: {
      siteName: 'Family Assistant',
      defaultLanguage: 'English',
      theme: flavor,
      timezone: 'America/New_York',
      autoRefresh: true,
      refreshInterval: 30
    },
    notifications: {
      emailAlerts: true,
      systemAlerts: true,
      securityAlerts: true,
      weeklyReports: false,
      maintenanceMode: false
    },
    security: {
      twoFactorAuth: false,
      sessionTimeout: 24,
      allowedIps: '',
      enableAuditLog: true,
      privacyMode: 'family'
    },
    ai: {
      defaultModel: 'family-assistant',
      maxTokens: 2048,
      temperature: 0.7,
      enableMemory: true,
      autoSaveConversations: true,
      contentFiltering: true
    },
    storage: {
      maxFileSize: 10,
      retentionDays: 365,
      compressionEnabled: true,
      backupFrequency: 'daily',
      storageLocation: 'local'
    },
    monitoring: {
      enableMetrics: true,
      enableLogging: true,
      logLevel: 'info',
      performanceMonitoring: true,
      healthChecks: true,
      alertThresholds: {
        cpu: 80,
        memory: 85,
        disk: 90
      }
    }
  });

  const sections: SettingsSection[] = [
    {
      id: 'general',
      title: 'General',
      icon: SettingsIcon,
      description: 'Basic system settings and preferences',
      settings: [
        {
          key: 'siteName',
          label: 'Site Name',
          type: 'text',
          value: settingsData.general.siteName,
          description: 'Name displayed in the header and title'
        },
        {
          key: 'defaultLanguage',
          label: 'Default Language',
          type: 'select',
          value: settingsData.general.defaultLanguage,
          options: ['English', 'Spanish', 'French', 'German'],
          description: 'Default interface language'
        },
        {
          key: 'theme',
          label: 'Catppuccin Theme',
          type: 'select',
          value: settingsData.general.theme,
          options: ['mocha', 'macchiato', 'frappe', 'latte'],
          description: 'Catppuccin color theme flavor'
        },
        {
          key: 'autoRefresh',
          label: 'Auto-refresh Dashboard',
          type: 'toggle',
          value: settingsData.general.autoRefresh,
          description: 'Automatically refresh dashboard data'
        },
        {
          key: 'refreshInterval',
          label: 'Refresh Interval (seconds)',
          type: 'number',
          value: settingsData.general.refreshInterval,
          description: 'How often to refresh dashboard data'
        }
      ]
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: Bell,
      description: 'Configure system alerts and notifications',
      settings: [
        {
          key: 'emailAlerts',
          label: 'Email Alerts',
          type: 'toggle',
          value: settingsData.notifications.emailAlerts,
          description: 'Send important alerts via email'
        },
        {
          key: 'systemAlerts',
          label: 'System Alerts',
          type: 'toggle',
          value: settingsData.notifications.systemAlerts,
          description: 'Show system alerts in dashboard'
        },
        {
          key: 'securityAlerts',
          label: 'Security Alerts',
          type: 'toggle',
          value: settingsData.notifications.securityAlerts,
          description: 'Alert on security events'
        },
        {
          key: 'weeklyReports',
          label: 'Weekly Reports',
          type: 'toggle',
          value: settingsData.notifications.weeklyReports,
          description: 'Send weekly usage and activity reports'
        }
      ]
    },
    {
      id: 'security',
      title: 'Security',
      icon: Shield,
      description: 'Security and privacy settings',
      settings: [
        {
          key: 'twoFactorAuth',
          label: 'Two-Factor Authentication',
          type: 'toggle',
          value: settingsData.security.twoFactorAuth,
          description: 'Require 2FA for all admin users'
        },
        {
          key: 'sessionTimeout',
          label: 'Session Timeout (hours)',
          type: 'number',
          value: settingsData.security.sessionTimeout,
          description: 'Automatically log out users after inactivity'
        },
        {
          key: 'enableAuditLog',
          label: 'Enable Audit Log',
          type: 'toggle',
          value: settingsData.security.enableAuditLog,
          description: 'Log all user actions for security review'
        },
        {
          key: 'privacyMode',
          label: 'Privacy Mode',
          type: 'select',
          value: settingsData.security.privacyMode,
          options: ['public', 'family', 'private'],
          description: 'Default privacy level for new content'
        }
      ]
    },
    {
      id: 'ai',
      title: 'AI Settings',
      icon: Zap,
      description: 'Configure AI behavior and models',
      settings: [
        {
          key: 'defaultModel',
          label: 'Default Model',
          type: 'select',
          value: settingsData.ai.defaultModel,
          options: ['family-assistant', 'gpt-4', 'claude-3'],
          description: 'Default AI model for conversations'
        },
        {
          key: 'maxTokens',
          label: 'Max Tokens',
          type: 'number',
          value: settingsData.ai.maxTokens,
          description: 'Maximum response length'
        },
        {
          key: 'temperature',
          label: 'Temperature',
          type: 'number',
          value: settingsData.ai.temperature,
          description: 'AI response randomness (0.0-1.0)'
        },
        {
          key: 'enableMemory',
          label: 'Enable Memory',
          type: 'toggle',
          value: settingsData.ai.enableMemory,
          description: 'Allow AI to remember past conversations'
        },
        {
          key: 'contentFiltering',
          label: 'Content Filtering',
          type: 'toggle',
          value: settingsData.ai.contentFiltering,
          description: 'Filter inappropriate content'
        }
      ]
    },
    {
      id: 'storage',
      title: 'Storage',
      icon: Database,
      description: 'Data storage and retention settings',
      settings: [
        {
          key: 'maxFileSize',
          label: 'Max File Size (MB)',
          type: 'number',
          value: settingsData.storage.maxFileSize,
          description: 'Maximum size for uploaded files'
        },
        {
          key: 'retentionDays',
          label: 'Data Retention (days)',
          type: 'number',
          value: settingsData.storage.retentionDays,
          description: 'Days to keep conversation history'
        },
        {
          key: 'compressionEnabled',
          label: 'Enable Compression',
          type: 'toggle',
          value: settingsData.storage.compressionEnabled,
          description: 'Compress stored data to save space'
        },
        {
          key: 'backupFrequency',
          label: 'Backup Frequency',
          type: 'select',
          value: settingsData.storage.backupFrequency,
          options: ['hourly', 'daily', 'weekly'],
          description: 'How often to create data backups'
        }
      ]
    },
    {
      id: 'monitoring',
      title: 'Monitoring',
      icon: Monitor,
      description: 'System monitoring and logging settings',
      settings: [
        {
          key: 'enableMetrics',
          label: 'Enable Metrics',
          type: 'toggle',
          value: settingsData.monitoring.enableMetrics,
          description: 'Collect system performance metrics'
        },
        {
          key: 'enableLogging',
          label: 'Enable Logging',
          type: 'toggle',
          value: settingsData.monitoring.enableLogging,
          description: 'Log system events and errors'
        },
        {
          key: 'logLevel',
          label: 'Log Level',
          type: 'select',
          value: settingsData.monitoring.logLevel,
          options: ['debug', 'info', 'warning', 'error'],
          description: 'Minimum level of logs to record'
        },
        {
          key: 'performanceMonitoring',
          label: 'Performance Monitoring',
          type: 'toggle',
          value: settingsData.monitoring.performanceMonitoring,
          description: 'Monitor application performance'
        }
      ]
    }
  ];

  const currentSection = sections.find(s => s.id === activeSection);

  const updateSetting = (sectionId: string, key: string, value: any) => {
    setSettingsData(prev => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        [key]: value
      }
    }));
    setHasUnsavedChanges(true);

    // Update theme immediately when changed
    if (sectionId === 'general' && key === 'theme') {
      setFlavor(value as any);
    }
  };

  const saveSettings = async () => {
    setSaveStatus('saving');
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveStatus('saved');
      setHasUnsavedChanges(false);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }
  };

  const resetSettings = () => {
    // Reset to defaults
    setSettingsData({
      general: {
        siteName: 'Family Assistant',
        defaultLanguage: 'English',
        theme: 'mocha',
        timezone: 'America/New_York',
        autoRefresh: true,
        refreshInterval: 30
      },
      notifications: {
        emailAlerts: true,
        systemAlerts: true,
        securityAlerts: true,
        weeklyReports: false,
        maintenanceMode: false
      },
      security: {
        twoFactorAuth: false,
        sessionTimeout: 24,
        allowedIps: '',
        enableAuditLog: true,
        privacyMode: 'family'
      },
      ai: {
        defaultModel: 'family-assistant',
        maxTokens: 2048,
        temperature: 0.7,
        enableMemory: true,
        autoSaveConversations: true,
        contentFiltering: true
      },
      storage: {
        maxFileSize: 10,
        retentionDays: 365,
        compressionEnabled: true,
        backupFrequency: 'daily',
        storageLocation: 'local'
      },
      monitoring: {
        enableMetrics: true,
        enableLogging: true,
        logLevel: 'info',
        performanceMonitoring: true,
        healthChecks: true,
        alertThresholds: {
          cpu: 80,
          memory: 85,
          disk: 90
        }
      }
    });
    setHasUnsavedChanges(false);
  };

  const renderSettingInput = (setting: any, sectionId: string) => {
    switch (setting.type) {
      case 'toggle':
        return (
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={setting.value}
              onChange={(e) => updateSetting(sectionId, setting.key, e.target.checked)}
              className="sr-only peer"
            />
            <div className="relative w-11 h-6 bg-ctp-surface1 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-ctp-blue/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-ctp-base after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-ctp-base after:border-ctp-surface1 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-ctp-blue"></div>
          </label>
        );

      case 'select':
        return (
          <select
            value={setting.value}
            onChange={(e) => updateSetting(sectionId, setting.key, e.target.value)}
            className="w-full px-3 py-2 bg-ctp-surface0 border border-ctp-surface1 text-ctp-text rounded-lg focus:ring-2 focus:ring-ctp-blue focus:border-ctp-blue outline-none"
          >
            {setting.options?.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'number':
        return (
          <input
            type="number"
            value={setting.value}
            onChange={(e) => updateSetting(sectionId, setting.key, parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 bg-ctp-surface0 border border-ctp-surface1 text-ctp-text rounded-lg focus:ring-2 focus:ring-ctp-blue focus:border-ctp-blue outline-none"
          />
        );

      case 'text':
        return (
          <input
            type="text"
            value={setting.value}
            onChange={(e) => updateSetting(sectionId, setting.key, e.target.value)}
            className="w-full px-3 py-2 bg-ctp-surface0 border border-ctp-surface1 text-ctp-text rounded-lg focus:ring-2 focus:ring-ctp-blue focus:border-ctp-blue outline-none"
          />
        );

      default:
        return null;
    }
  };

  const getSaveButtonContent = () => {
    switch (saveStatus) {
      case 'saving':
        return (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Saving...
          </>
        );
      case 'saved':
        return (
          <>
            <Check className="w-4 h-4" />
            Saved
          </>
        );
      case 'error':
        return (
          <>
            <X className="w-4 h-4" />
            Error
          </>
        );
      default:
        return (
          <>
            <Save className="w-4 h-4" />
            Save Changes
          </>
        );
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-ctp-text">Settings</h1>
          <p className="text-ctp-subtext1 mt-2">
            Configure your Family Assistant system
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={resetSettings}
            className="flex items-center gap-2 px-4 py-2 text-ctp-subtext1 hover:text-ctp-text border border-ctp-surface1 rounded-lg hover:bg-ctp-surface0 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={saveSettings}
            disabled={!hasUnsavedChanges || saveStatus === 'saving'}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              hasUnsavedChanges
                ? 'bg-ctp-blue text-ctp-base hover:bg-ctp-sapphire'
                : 'bg-ctp-surface1 text-ctp-overlay0 cursor-not-allowed'
            }`}
          >
            {getSaveButtonContent()}
          </button>
        </div>
      </div>

      {/* Unsaved Changes Warning */}
      {hasUnsavedChanges && (
        <div className="mb-6 p-4 bg-ctp-yellow/10 border border-ctp-yellow rounded-lg flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-ctp-yellow" />
          <p className="text-sm text-ctp-yellow">
            You have unsaved changes. Don't forget to save them before leaving.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg transition-colors ${
                    activeSection === section.id
                      ? 'bg-ctp-surface1 text-ctp-text border-l-4 border-ctp-blue'
                      : 'text-ctp-subtext1 hover:bg-ctp-surface0'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <div>
                    <div className="font-medium">{section.title}</div>
                    <div className="text-sm opacity-75">{section.description}</div>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          {currentSection && (
            <div className="bg-ctp-mantle border border-ctp-surface1 rounded-lg">
              <div className="p-6 border-b border-ctp-surface1">
                <div className="flex items-center gap-3">
                  <currentSection.icon className="w-6 h-6 text-ctp-subtext0" />
                  <div>
                    <h2 className="text-xl font-semibold text-ctp-text">
                      {currentSection.title}
                    </h2>
                    <p className="text-sm text-ctp-subtext1 mt-1">
                      {currentSection.description}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="space-y-6">
                  {currentSection.settings.map((setting) => (
                    <div key={setting.key}>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-ctp-text">
                          {setting.label}
                        </label>
                        {renderSettingInput(setting, currentSection.id)}
                      </div>
                      {setting.description && (
                        <p className="text-sm text-ctp-subtext0 flex items-start gap-1">
                          <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          {setting.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};