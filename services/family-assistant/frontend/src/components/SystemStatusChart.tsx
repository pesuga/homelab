import React from 'react';
import { SystemMetrics } from '@/types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

interface SystemStatusChartProps {
  data: SystemMetrics;
}

export const SystemStatusChart: React.FC<SystemStatusChartProps> = ({ data }) => {
  // Generate sample historical data for the chart
  const generateHistoricalData = () => {
    const now = Date.now();
    const dataPoints = [];

    for (let i = 23; i >= 0; i--) {
      const timestamp = now - (i * 60 * 60 * 1000); // Hours ago
      dataPoints.push({
        time: new Date(timestamp).getHours() + ':00',
        cpu: Math.max(0, data.cpu.usage + (Math.random() - 0.5) * 20),
        memory: Math.max(0, data.memory.percentage + (Math.random() - 0.5) * 15),
        disk: data.disk.percentage, // Disk doesn't change much
      });
    }

    return dataPoints;
  };

  const chartData = generateHistoricalData();

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis
          dataKey="time"
          stroke="#6b7280"
          fontSize={12}
        />
        <YAxis
          stroke="#6b7280"
          fontSize={12}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="cpu"
          stackId="1"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.6}
          name="CPU %"
        />
        <Area
          type="monotone"
          dataKey="memory"
          stackId="1"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.6}
          name="Memory %"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};