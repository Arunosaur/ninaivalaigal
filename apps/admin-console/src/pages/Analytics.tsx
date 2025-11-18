// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import SecurityHealthGauge from '../components/SecurityHealthGauge'
import SecurityTimeSeriesChart from '../components/SecurityTimeSeriesChart'
import SuspiciousIPsTable from '../components/SuspiciousIPsTable'
import FailedLoginsTable from '../components/FailedLoginsTable'
import useSecurityMetrics from '../hooks/useSecurityMetrics'

const DEFAULT_TIME_WINDOWS = [24, 168, 720]

export default function Analytics() {
  const [timeWindow, setTimeWindow] = useState<number>(24)
  const { metrics, loading, error, lastUpdated, refetch, isRefreshing } = useSecurityMetrics(timeWindow)

  useEffect(() => {
    setTimeWindow((previous) => (DEFAULT_TIME_WINDOWS.includes(previous) ? previous : 24))
  }, [])

  const aggregatedCounts = useMemo(() => {
    if (!metrics?.events_by_type) {
      return null
    }

    return Object.entries(metrics.events_by_type).map(([eventType, counts]) => ({
      eventType,
      total: counts.event_count ?? 0,
      uniqueUsers: counts.unique_users ?? 0,
      uniqueIps: counts.unique_ips ?? 0,
    }))
  }, [metrics])

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Ninaivalaigal Admin Console</h1>
            <nav className="flex space-x-4">
              <Link to="/analytics" className="text-blue-400 hover:text-blue-300 px-3 py-2 rounded-md text-sm font-medium">
                Analytics
              </Link>
              <Link to="/teams" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Teams
              </Link>
              <Link to="/users" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Users
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Security Monitoring Dashboard</h2>
            <p className="text-gray-400">
              Live security posture, authentication trends, and suspicious activity insights
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-gray-400">
              Time Window:
              <select
                className="ml-2 rounded-md border border-gray-700 bg-gray-800 px-3 py-1 text-sm text-gray-200 focus:border-blue-500 focus:outline-none"
                value={timeWindow}
                onChange={(event) => {
                  const value = Number(event.target.value)
                  setTimeWindow(value)
                  void refetch()
                }}
              >
                <option value={24}>Last 24 Hours</option>
                <option value={168}>Last 7 Days</option>
                <option value={720}>Last 30 Days</option>
              </select>
            </label>

            <button
              type="button"
              className="rounded-md border border-blue-500 bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400"
              onClick={() => {
                void refetch()
              }}
              disabled={isRefreshing}
            >
              {isRefreshing ? 'Refreshing…' : 'Refresh'}
            </button>

            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Updated {lastUpdated.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <p className="text-yellow-400 text-sm">{error}</p>
          </div>
        )}

        {/* Metrics Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {metrics ? (
              <>
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-4 mb-8">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 lg:col-span-1 flex items-center justify-center">
                    <SecurityHealthGauge score={metrics.security_health_score} />
                  </div>

                  <MetricCard
                    title="Auth Failures"
                    subtitle="Last 24 Hours"
                    value={metrics.auth_failures_24h.toLocaleString()}
                    badge={`${metrics.auth_failures_7d.toLocaleString()} last 7d`}
                  />

                  <MetricCard
                    title="Success Rate"
                    subtitle="Authentication"
                    value={`${metrics.auth_success_rate.toFixed(1)}%`}
                    badge={`${metrics.auth_failures_30d.toLocaleString()} failures 30d`}
                  />

                  <MetricCard
                    title="Active Incidents"
                    subtitle="Account Lockouts"
                    value={metrics.active_security_incidents.toString()}
                    badge={`${metrics.rate_limit_exceeded_count} rate limit events`}
                  />
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-8">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Security Events by Hour</h3>
                      <span className="text-xs text-gray-500">Aggregated per event type</span>
                    </div>
                    <SecurityTimeSeriesChart data={metrics.time_series} timeWindowHours={metrics.time_window_hours} />
                  </div>

                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Aggregated Events</h3>
                    <ul className="space-y-3 text-sm text-gray-200">
                      {aggregatedCounts?.map((item) => (
                        <li key={item.eventType} className="flex flex-col rounded-lg border border-gray-700 bg-gray-900/60 p-3">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">{item.eventType.replace(/_/g, ' ')}</span>
                            <span className="text-xs text-gray-400">{item.total} events</span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-400">
                            <span>{item.uniqueUsers} unique users</span>
                            <span>{item.uniqueIps} unique IPs</span>
                          </div>
                        </li>
                      )) || <li className="text-gray-500">No event aggregates available.</li>}
                    </ul>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">Suspicious IPs</h3>
                      <span className="text-xs text-gray-500">Threshold ≥ 10 events</span>
                    </div>
                    <SuspiciousIPsTable items={metrics.suspicious_ips} />
                  </div>

                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">Failed Logins (Top 10)</h3>
                      <span className="text-xs text-gray-500">Risk ranked by frequency</span>
                    </div>
                    <FailedLoginsTable items={metrics.failed_logins_by_user} />
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-gray-400">Security metrics unavailable.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

interface MetricCardProps {
  title: string
  subtitle?: string
  value: string
  badge?: string
}

function MetricCard({ title, subtitle, value, badge }: MetricCardProps) {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <p className="text-sm font-medium text-gray-400">{title}</p>
      {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
      <p className="mt-3 text-3xl font-bold text-white">{value}</p>
      {badge && <span className="mt-2 inline-flex text-xs text-gray-400">{badge}</span>}
    </div>
  )
}
