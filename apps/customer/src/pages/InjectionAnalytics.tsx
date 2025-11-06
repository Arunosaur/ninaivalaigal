// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#350: Injection Analytics Dashboard (SPEC-036)
 *
 * Dashboard for viewing memory injection analytics, performance metrics,
 * and effectiveness tracking.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Navigation } from '../components/Navigation';
import apiClient from '../lib/apiClient';

interface InjectionAnalytics {
  total_injections: number;
  successful_injections: number;
  failed_injections: number;
  average_response_time_ms: number;
  injection_by_strategy: Record<string, number>;
  injection_by_trigger: Record<string, number>;
  effectiveness_score: number;
  period_start: string;
  period_end: string;
}

interface InjectionHistory {
  date: string;
  count: number;
  success_rate: number;
  avg_response_time_ms: number;
}

export default function InjectionAnalytics() {
  const [analytics, setAnalytics] = useState<InjectionAnalytics | null>(null);
  const [history, setHistory] = useState<InjectionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    loadAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [analyticsRes, historyRes] = await Promise.all([
        apiClient.get<InjectionAnalytics>(`/api/v1/memory/injection-analytics?period=${period}`),
        apiClient.get<{ history: InjectionHistory[] }>(`/api/v1/memory/injection-history?period=${period}`),
      ]);

      setAnalytics(analyticsRes.data);
      setHistory(historyRes.data.history || []);
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value: number, total: number) => {
    if (total === 0) return '0%';
    return `${((value / total) * 100).toFixed(1)}%`;
  };

  const getEffectivenessColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-rose-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
        <Navigation variant="dark" className="sticky top-0 z-20" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex items-center justify-center py-20">
            <div className="h-12 w-12 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Navigation variant="dark" className="sticky top-0 z-20" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Injection Analytics
              </h1>
              <p className="text-slate-400 mt-2">Memory injection performance and effectiveness metrics</p>
            </div>
            <div className="flex items-center space-x-2">
              {(['7d', '30d', '90d'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                    period === p
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                      : 'border border-white/20 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
                </button>
              ))}
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        {analytics && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                <div className="text-sm text-slate-400 mb-1">Total Injections</div>
                <div className="text-3xl font-bold text-white">{analytics.total_injections.toLocaleString()}</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                <div className="text-sm text-slate-400 mb-1">Success Rate</div>
                <div className="text-3xl font-bold text-emerald-400">
                  {formatPercentage(analytics.successful_injections, analytics.total_injections)}
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                <div className="text-sm text-slate-400 mb-1">Avg Response Time</div>
                <div className="text-3xl font-bold text-white">
                  {analytics.average_response_time_ms.toFixed(0)}ms
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                <div className="text-sm text-slate-400 mb-1">Effectiveness Score</div>
                <div className={`text-3xl font-bold ${getEffectivenessColor(analytics.effectiveness_score)}`}>
                  {analytics.effectiveness_score.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Strategy Breakdown */}
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Injection by Strategy</h2>
              <div className="space-y-3">
                {Object.entries(analytics.injection_by_strategy).map(([strategy, count]) => (
                  <div key={strategy} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 capitalize">{strategy}</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-48 bg-slate-800 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-indigo-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{
                            width: `${(count / analytics.total_injections) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium text-white w-16 text-right">
                        {count.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trigger Breakdown */}
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Injection by Trigger</h2>
              <div className="space-y-3">
                {Object.entries(analytics.injection_by_trigger).map(([trigger, count]) => (
                  <div key={trigger} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 capitalize">{trigger}</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-48 bg-slate-800 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-600 to-cyan-600 h-2 rounded-full transition-all duration-300"
                          style={{
                            width: `${(count / analytics.total_injections) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium text-white w-16 text-right">
                        {count.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* History Chart Placeholder */}
            {history.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
                <h2 className="text-xl font-semibold text-white mb-4">Injection History</h2>
                <div className="space-y-2">
                  {history.slice(-10).reverse().map((entry) => (
                    <div key={entry.date} className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{new Date(entry.date).toLocaleDateString()}</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-slate-300">{entry.count} injections</span>
                        <span className="text-emerald-400">{entry.success_rate.toFixed(1)}% success</span>
                        <span className="text-slate-400">{entry.avg_response_time_ms.toFixed(0)}ms avg</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Back Link */}
        <div className="mt-10">
          <Link
            to="/memory-browser"
            className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 transition-colors duration-300"
          >
            <span>←</span>
            <span>Back to Memory Browser</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
