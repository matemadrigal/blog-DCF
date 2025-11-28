"use client";

import { useState } from 'react';
import { TrendingUp, Search, Calculator, Download } from 'lucide-react';
import { apiClient, DCFCalculationRequest, DCFResult } from '@/lib/api';
import { formatCurrency, formatPercent, getRecommendationColor, getUpsideColor } from '@/lib/utils';

export default function AnalysisPage() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DCFResult | null>(null);
  const [error, setError] = useState('');

  // DCF Parameters
  const [useIntelligent, setUseIntelligent] = useState(true);
  const [projectionYears, setProjectionYears] = useState(5);
  const [growthRate, setGrowthRate] = useState(0.05);
  const [terminalGrowth, setTerminalGrowth] = useState(0.025);
  const [discountRate, setDiscountRate] = useState(0.08);

  const handleCalculate = async () => {
    if (!ticker.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const request: DCFCalculationRequest = {
        ticker: ticker.toUpperCase(),
        projection_years: projectionYears,
        use_intelligent_values: useIntelligent,
      };

      if (!useIntelligent) {
        request.growth_rate = growthRate;
        request.terminal_growth_rate = terminalGrowth;
        request.discount_rate = discountRate;
      }

      const data = await apiClient.calculateDCF(request);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate DCF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0A0E27] via-[#0A0E27] to-[#0d1234] py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold gradient-text mb-4">
            Individual Analysis
          </h1>
          <p className="text-xl text-gray-300">
            Calculate the Fair Value of a stock using DCF and compare it with market price
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1 space-y-6">
            {/* Ticker Input */}
            <div className="bg-dark-card border border-dark-border rounded-xl p-6 space-y-4">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Search className="w-5 h-5 text-primary-500" />
                Company Ticker
              </h2>

              <div className="relative">
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && handleCalculate()}
                  placeholder="e.g., AAPL"
                  className="w-full px-4 py-3 bg-dark-background border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <button
                onClick={handleCalculate}
                disabled={loading}
                className="w-full px-6 py-3 bg-gradient-primary text-white rounded-lg font-semibold flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Calculator className="w-5 h-5" />
                    Calculate DCF
                  </>
                )}
              </button>

              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
            </div>

            {/* Parameters */}
            <div className="bg-dark-card border border-dark-border rounded-xl p-6 space-y-4">
              <h2 className="text-xl font-semibold text-white">Parameters</h2>

              <div className="flex items-center justify-between">
                <label className="text-gray-300">Use Intelligent Values</label>
                <button
                  onClick={() => setUseIntelligent(!useIntelligent)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useIntelligent ? 'bg-primary-500' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useIntelligent ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {!useIntelligent && (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Growth Rate (%)</label>
                    <input
                      type="number"
                      value={growthRate * 100}
                      onChange={(e) => setGrowthRate(Number(e.target.value) / 100)}
                      step="0.1"
                      className="w-full px-3 py-2 bg-dark-background border border-dark-border rounded-lg text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Terminal Growth (%)</label>
                    <input
                      type="number"
                      value={terminalGrowth * 100}
                      onChange={(e) => setTerminalGrowth(Number(e.target.value) / 100)}
                      step="0.1"
                      className="w-full px-3 py-2 bg-dark-background border border-dark-border rounded-lg text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Discount Rate (%)</label>
                    <input
                      type="number"
                      value={discountRate * 100}
                      onChange={(e) => setDiscountRate(Number(e.target.value) / 100)}
                      step="0.1"
                      className="w-full px-3 py-2 bg-dark-background border border-dark-border rounded-lg text-white"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-2">Projection Years</label>
                <input
                  type="number"
                  value={projectionYears}
                  onChange={(e) => setProjectionYears(Number(e.target.value))}
                  min="3"
                  max="10"
                  className="w-full px-3 py-2 bg-dark-background border border-dark-border rounded-lg text-white"
                />
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Main Results */}
                <div className="bg-dark-card border border-dark-border rounded-xl p-8">
                  <div className="flex items-start justify-between mb-8">
                    <div>
                      <h2 className="text-3xl font-bold text-white mb-2">
                        {result.company_name}
                      </h2>
                      <p className="text-gray-400">Ticker: {result.ticker}</p>
                    </div>
                    <div className={`px-4 py-2 rounded-lg font-semibold ${
                      result.recommendation === 'Strong Buy' ? 'bg-green-500/20 text-green-400' :
                      result.recommendation === 'Buy' ? 'bg-green-500/10 text-green-400' :
                      result.recommendation === 'Hold' ? 'bg-yellow-500/20 text-yellow-400' :
                      result.recommendation === 'Sell' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {result.recommendation}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6 mb-8">
                    <div className="space-y-2">
                      <p className="text-sm text-gray-400">Current Price</p>
                      <p className="text-3xl font-bold text-white">
                        {formatCurrency(result.current_price)}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm text-gray-400">Fair Value</p>
                      <p className="text-3xl font-bold gradient-text">
                        {formatCurrency(result.fair_value)}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm text-gray-400">Upside/Downside</p>
                      <p className={`text-3xl font-bold ${getUpsideColor(result.upside_percentage)}`}>
                        {formatPercent(result.upside_percentage)}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm text-gray-400">Confidence Score</p>
                      <p className="text-3xl font-bold text-primary-500">
                        {(result.confidence_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  {/* Parameters Used */}
                  <div className="border-t border-dark-border pt-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Parameters Used</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-400">Growth Rate</p>
                        <p className="text-white font-medium">{formatPercent(result.growth_rate * 100)}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Terminal Growth</p>
                        <p className="text-white font-medium">{formatPercent(result.terminal_growth_rate * 100)}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Discount Rate</p>
                        <p className="text-white font-medium">{formatPercent(result.discount_rate * 100)}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Projection Years</p>
                        <p className="text-white font-medium">{result.projection_years}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Financial Metrics */}
                {(result.fcf_current || result.revenue_current || result.shares_outstanding) && (
                  <div className="bg-dark-card border border-dark-border rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Financial Metrics</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {result.fcf_current && (
                        <div>
                          <p className="text-sm text-gray-400 mb-1">Free Cash Flow</p>
                          <p className="text-xl font-bold text-white">
                            ${(result.fcf_current / 1e9).toFixed(2)}B
                          </p>
                        </div>
                      )}
                      {result.revenue_current && (
                        <div>
                          <p className="text-sm text-gray-400 mb-1">Revenue</p>
                          <p className="text-xl font-bold text-white">
                            ${(result.revenue_current / 1e9).toFixed(2)}B
                          </p>
                        </div>
                      )}
                      {result.shares_outstanding && (
                        <div>
                          <p className="text-sm text-gray-400 mb-1">Shares Outstanding</p>
                          <p className="text-xl font-bold text-white">
                            {(result.shares_outstanding / 1e9).toFixed(2)}B
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-dark-card border border-dark-border rounded-xl p-12 text-center">
                <TrendingUp className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">
                  Enter a ticker symbol and click "Calculate DCF" to see the analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
