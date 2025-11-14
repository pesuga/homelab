import React from 'react';
import { X, AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';
import { Alert } from '@/types';

interface AlertBannerProps {
  alerts: Alert[];
  onDismiss: (id: string) => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alerts, onDismiss }) => {
  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getAlertStyles = (type: Alert['type']) => {
    switch (type) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (alerts.length === 0) return null;

  return (
    <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-4xl">
      <div className="space-y-2 px-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`flex items-start gap-3 p-4 rounded-lg border ${getAlertStyles(
              alert.type
            )} shadow-lg fade-in`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getAlertIcon(alert.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium">{alert.title}</h3>
                {alert.service && (
                  <span className="text-xs px-2 py-1 bg-ctp-mantle/50 rounded-full">
                    {alert.service}
                  </span>
                )}
              </div>
              <p className="text-sm mt-1">{alert.message}</p>
              <p className="text-xs mt-1 opacity-75">
                {formatTimestamp(alert.timestamp)}
              </p>
            </div>
            <div className="flex-shrink-0">
              <button
                onClick={() => onDismiss(alert.id)}
                className="inline-flex text-gray-400 hover:text-ctp-subtext1 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent"
              >
                <span className="sr-only">Dismiss</span>
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};