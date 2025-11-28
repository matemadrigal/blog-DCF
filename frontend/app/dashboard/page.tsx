"use client";

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { apiClient, DashboardSummary } from '@/lib/api';
import { formatCurrency, formatPercent, getRecommendationColor } from '@/lib/utils';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await apiClient.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234] py-12 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234] py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-8 text-center">
            <p className="text-red-400 text-lg">{error}</p>
            <button
              onClick={loadDashboard}
              className="mt-4 px-6 py-2 bg-gradient-primary text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!summary || summary.total_companies === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234] py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <h1 className="text-5xl font-bold gradient-text mb-12">Executive Dashboard</h1>
          <div className="bg-dark-card border border-dark-border rounded-xl p-12 text-center">
            <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-4">
              No companies analyzed yet
            </p>
            <p className="text-gray-500 mb-6">
              Start by analyzing some companies in the Individual Analysis section
            </p>
            <a
              href="/analysis"
              className="inline-block px-8 py-3 bg-gradient-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity"
            >
              Analyze Companies
            </a>
          </div>
        </div>
      </div>
    );
  }

  const recommendationDistribution = [
    { label: 'Strong Buy', count: summary.strong_buys, color: 'bg-green-500' },
    { label: 'Buy', count: summary.buys, color: 'bg-green-400' },
    { label: 'Hold', count: summary.holds, color: 'bg-yellow-500' },
    { label: 'Sell', count: summary.sells, color: 'bg-orange-500' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234] py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold gradient-text mb-4">
            Executive Dashboard
          </h1>
          <p className="text-xl text-gray-300">
            Consolidated overview of all analyzed companies
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-400">Total Companies</p>
              <BarChart3 className="w-5 h-5 text-primary-500" />
            </div>
            <p className="text-4xl font-bold text-white">{summary.total_companies}</p>
          </div>

          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-400">Avg Upside</p>
              {summary.avg_upside >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-500" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-500" />
              )}
            </div>
            <p className={`text-4xl font-bold ${summary.avg_upside >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {formatPercent(summary.avg_upside)}
            </p>
          </div>

          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-400">Strong Buys</p>
              <div className="w-3 h-3 rounded-full bg-green-500" />
            </div>
            <p className="text-4xl font-bold text-white">{summary.strong_buys}</p>
          </div>

          <div className="bg-dark-card border border-dark-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-400">Buys</p>
              <div className="w-3 h-3 rounded-full bg-green-400" />
            </div>
            <p className="text-4xl font-bold text-white">{summary.buys}</p>
          </div>
        </div>

        {/* Recommendation Distribution */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-6 mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Recommendation Distribution</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {recommendationDistribution.map((item) => (
              <div key={item.label} className="text-center">
                <div className={`h-2 rounded-full mb-3 ${item.color}`} style={{ width: `${(item.count / summary.total_companies) * 100}%`, minWidth: '20px' }} />
                <p className="text-sm text-gray-400 mb-1">{item.label}</p>
                <p className="text-2xl font-bold text-white">{item.count}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Top Opportunities */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Top Investment Opportunities</h2>

          <div className="space-y-4">
            {summary.top_opportunities.map((opportunity, index) => (
              <div
                key={opportunity.ticker}
                className="bg-dark-background border border-dark-border rounded-lg p-6 hover:border-primary-500 transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold gradient-text">#{index + 1}</span>
                      <div>
                        <h3 className="text-xl font-bold text-white">{opportunity.ticker}</h3>
                        <p className="text-gray-400">{opportunity.company_name}</p>
                      </div>
                    </div>
                  </div>

                  <div className={`px-4 py-2 rounded-lg font-semibold ${
                    opportunity.recommendation === 'Strong Buy' ? 'bg-green-500/20 text-green-400' :
                    opportunity.recommendation === 'Buy' ? 'bg-green-500/10 text-green-400' :
                    opportunity.recommendation === 'Hold' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-orange-500/20 text-orange-400'
                  }`}>
                    {opportunity.recommendation}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Current Price</p>
                    <p className="text-lg font-bold text-white">
                      {formatCurrency(opportunity.current_price)}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-400 mb-1">Fair Value</p>
                    <p className="text-lg font-bold gradient-text">
                      {formatCurrency(opportunity.fair_value)}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-400 mb-1">Upside</p>
                    <p className={`text-lg font-bold ${opportunity.upside_percentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {formatPercent(opportunity.upside_percentage)}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-400 mb-1">Confidence</p>
                    <p className="text-lg font-bold text-primary-500">
                      {(opportunity.confidence_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
