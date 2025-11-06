// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import type { AxiosError } from 'axios'
import { Navigation } from '../components/Navigation'
import apiClient from '../lib/apiClient'

interface TeamStats {
  total_memories: number
  active_sessions: number
  team_members: number
  storage_used_mb: number
  api_calls_today: number
  subscription_tier: string
}

interface Memory {
  id: string
  content: string
  context: string
  created_at: string
  tags: string[]
}

const SAMPLE_TEAM_STATS: TeamStats = {
  total_memories: 1284,
  active_sessions: 7,
  team_members: 24,
  storage_used_mb: 812.45,
  api_calls_today: 1864,
  subscription_tier: 'enterprise',
}

export default function Dashboard() {
  const [stats, setStats] = useState<TeamStats | null>(null)
  const [recentMemories, setRecentMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [usingFallback, setUsingFallback] = useState(false)

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()

    async function loadStats() {
      try {
        setLoading(true)
        const response = await apiClient.get<TeamStats>('/users/me/stats', { signal: controller.signal })
        if (!isMounted) {
          return
        }
        setStats(response.data)
        setError(null)
        setUsingFallback(false)
      } catch (err) {
        if (!isMounted) {
          return
        }
        const axiosError = err as AxiosError<{ detail?: string }>
        const message = axiosError.response?.data?.detail || axiosError.message || 'Unable to load dashboard stats'
        setError(message)
        setStats(SAMPLE_TEAM_STATS)
        setUsingFallback(true)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    async function loadRecentMemories() {
      try {
        const response = await apiClient.get<{ memories: Memory[] }>('/api/v1/memory/memories', {
          signal: controller.signal,
          params: { limit: 5 }
        })
        if (!isMounted) {
          return
        }
        setRecentMemories(response.data.memories || [])
      } catch (err) {
        console.error('Failed to load recent memories:', err)
      }
    }

    loadStats()
    loadRecentMemories()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [])

  function formatTimeAgo(dateString: string): string {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

  const errorId = 'dashboard-error';
  const loadingId = 'dashboard-loading';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <Navigation variant="dark" className="sticky top-0 z-10" />

      {/* Main Content */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Welcome Back
          </h1>
          <p className="text-gray-400 text-lg">Your enterprise memory management at a glance</p>
        </div>

        {loading ? (
          <div
            id={loadingId}
            className="flex items-center justify-center h-64"
            role="status"
            aria-live="polite"
            aria-label="Loading dashboard data"
          >
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" aria-hidden="true"></div>
            <span className="sr-only">Loading dashboard...</span>
          </div>
        ) : stats ? (
          <>
            {usingFallback ? (
              <div
                role="alert"
                aria-live="polite"
                className="mb-8 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200"
              >
                API connection failed ({error}). Displaying sample enterprise telemetry for development.
              </div>
            ) : null}
            {/* Stats Grid */}
            <section aria-labelledby="dashboard-stats-heading">
              <h2 id="dashboard-stats-heading" className="sr-only">Dashboard Statistics</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8" role="list">
                <div role="listitem">
                  <StatCard
                    title="Total Memories"
                    value={stats?.total_memories.toLocaleString() || '0'}
                    icon="💾"
                    trend="+12%"
                    trendUp={true}
                  />
                </div>
                <div role="listitem">
                  <StatCard
                    title="Active Sessions"
                    value={stats?.active_sessions.toString() || '0'}
                    icon="⚡"
                    trend="+5%"
                    trendUp={true}
                  />
                </div>
                <div role="listitem">
                  <StatCard
                    title="Team Members"
                    value={stats?.team_members.toString() || '0'}
                    icon="👥"
                    trend="2 new"
                    trendUp={true}
                  />
                </div>
                <div role="listitem">
                  <StatCard
                    title="Storage Used"
                    value={`${((stats?.storage_used_mb || 0)).toFixed(2)} MB`}
                    icon="📊"
                    trend="Daily snapshot"
                    trendUp={false}
                  />
                </div>
                <div role="listitem">
                  <StatCard
                    title="API Calls Today"
                    value={stats?.api_calls_today.toLocaleString() || '0'}
                    icon="🔄"
                    trend="+8%"
                    trendUp={true}
                  />
                </div>
                <div role="listitem">
                  <Link to="/team/billing" aria-label="View billing plan and upgrade options">
                    <StatCard
                      title="Plan"
                      value={(stats?.subscription_tier ?? 'pro').toUpperCase()}
                      icon="⭐"
                      trend="Upgrade available →"
                      trendUp={false}
                    />
                  </Link>
                </div>
              </div>
            </section>

            {/* Quick Actions */}
            <section aria-labelledby="quick-actions-heading">
              <h2 id="quick-actions-heading" className="sr-only">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8" role="list">
                <div role="listitem">
                  <Link
                    to="/memory-browser"
                    className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl p-4 text-center transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800 block"
                    aria-label="Open Memory Browser"
                  >
                    <div className="text-2xl mb-2" aria-hidden="true">📖</div>
                    <div className="font-semibold">Memory Browser</div>
                  </Link>
                </div>
                <div role="listitem">
                  <Link
                    to="/teams"
                    className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-xl p-4 text-center transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 block"
                    aria-label="Manage Teams"
                  >
                    <div className="text-2xl mb-2" aria-hidden="true">👥</div>
                    <div className="font-semibold">Teams</div>
                  </Link>
                </div>
                <div role="listitem">
                  <Link
                    to="/injection-analytics"
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl p-4 text-center transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 block"
                    aria-label="View Injection Analytics"
                  >
                    <div className="text-2xl mb-2" aria-hidden="true">📊</div>
                    <div className="font-semibold">Injection Analytics</div>
                  </Link>
                </div>
                <div role="listitem">
                  <Link
                    to="/settings"
                    className="bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-xl p-4 text-center transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-800 block"
                    aria-label="Open Settings"
                  >
                    <div className="text-2xl mb-2" aria-hidden="true">⚙️</div>
                    <div className="font-semibold">Settings</div>
                  </Link>
                </div>
              </div>
            </section>

            {/* Recent Activity */}
            <section aria-labelledby="recent-activity-heading">
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 shadow-2xl">
                <h2 id="recent-activity-heading" className="text-xl font-semibold text-white mb-4">
                  Recent Activity
                </h2>
                <div className="space-y-3" role="list" aria-live="polite">
                  {recentMemories.length > 0 ? (
                    recentMemories.slice(0, 3).map((memory) => (
                      <ActivityItem
                        key={memory.id}
                        action="Memory created"
                        details={memory.content.substring(0, 60) + (memory.content.length > 60 ? '...' : '')}
                        time={formatTimeAgo(memory.created_at)}
                      />
                    ))
                  ) : (
                    <ActivityItem
                      action="No recent activity"
                      details="Create your first memory to get started"
                      time="—"
                    />
                  )}
                </div>
              </div>
            </section>
          </>
        ) : (
          <div
            id={errorId}
            role="alert"
            aria-live="polite"
            className="flex items-center justify-center h-64"
          >
            <p className="text-rose-300 text-sm font-medium">{error ?? 'Unable to load dashboard stats'}</p>
          </div>
        )}
      </main>
    </div>
  )
}

function StatCard({ title, value, icon, trend, trendUp }: {
  title: string
  value: string
  icon: string
  trend: string
  trendUp: boolean
}) {
  return (
    <article className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 shadow-xl hover:shadow-2xl transition-all hover:scale-105 cursor-pointer focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 focus-within:ring-offset-gray-800">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
        <span className="text-2xl" aria-hidden="true">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-white mb-2" aria-label={`${title}: ${value}`}>{value}</p>
      <p className={`text-sm ${trendUp ? 'text-green-400' : 'text-indigo-400'}`} aria-label={`Trend: ${trend}`}>
        {trend}
      </p>
    </article>
  )
}

function ActivityItem({ action, details, time }: {
  action: string
  details: string
  time: string
}) {
  return (
    <article className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-700/30 transition" role="listitem">
      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" aria-hidden="true"></div>
      <div className="flex-1">
        <p className="text-white font-medium">{action}</p>
        <p className="text-gray-400 text-sm">{details}</p>
      </div>
      <time className="text-gray-500 text-xs" dateTime={time}>{time}</time>
    </article>
  )
}
