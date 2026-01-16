/**
 * Admin Metrics Page
 */
import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { adminAPI } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import type { MetricsResponse } from '@/types';

export const AdminMetricsPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await adminAPI.getMetrics();
      setMetrics(data);
    } catch (error) {
      toast.error('Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const metricCards = [
    { label: 'Total Users', value: metrics.total_users },
    { label: 'Active Users (7d)', value: metrics.active_users_7d },
    { label: 'Queries (All Time)', value: metrics.total_queries_all_time },
    { label: 'Queries (Today)', value: metrics.total_queries_today },
    { label: 'Queries (Week)', value: metrics.total_queries_week },
    { label: 'Primary Acceptance Rate', value: `${metrics.primary_acceptance_rate.toFixed(1)}%` },
    { label: 'Final Acceptance Rate', value: `${metrics.final_acceptance_rate.toFixed(1)}%` },
    { label: 'Avg Library Size', value: metrics.avg_library_size.toFixed(1) },
    { label: 'Avg Rating', value: `${metrics.avg_rating.toFixed(2)}/10` },
    { label: 'Median Rating', value: `${metrics.median_rating.toFixed(1)}/10` },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">System Metrics</h1>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {metricCards.map((metric, idx) => (
            <div
              key={idx}
              className="bg-white rounded-lg shadow-md p-6"
            >
              <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
              <p className="text-3xl font-bold text-gray-900">{metric.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
