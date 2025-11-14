import React from 'react';
import { ServiceStatus } from '@/types';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface ServiceGridProps {
  services: ServiceStatus[];
}

export const ServiceGrid: React.FC<ServiceGridProps> = ({ services }) => {
  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-ctp-subtext0" />;
    }
  };

  const getStatusText = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'running':
        return 'Running';
      case 'error':
        return 'Error';
      case 'warning':
        return 'Warning';
      case 'stopped':
        return 'Stopped';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {services.map((service) => (
        <div
          key={service.name}
          className="flex items-center justify-between p-4 bg-ctp-mantle rounded-lg border border-ctp-surface1 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center gap-3">
            {getStatusIcon(service.status)}
            <div>
              <h3 className="font-medium text-ctp-text">{service.name}</h3>
              <p className="text-sm text-ctp-subtext0">{getStatusText(service.status)}</p>
            </div>
          </div>
          {service.responseTime && (
            <div className="text-right">
              <p className="text-xs text-ctp-subtext0">Response Time</p>
              <p className="text-sm font-medium">{service.responseTime}ms</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};