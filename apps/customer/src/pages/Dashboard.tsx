// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { useState, useEffect } from 'react'
import { Navigation } from '../components/Navigation'

interface TeamStats {
  total_memories: number
  active_sessions: number
  team_members: number
  storage_used_mb: number
  api_calls_today: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<TeamStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Replace with actual API call when authenticated
    // For now, use mock data
    setTimeout(() => {
      setStats({
        total_memories: 1234,
        active_sessions: 42,
        team_members: 8,
        storage_used_mb: 2048,
        api_calls_today: 15420,
      })
      setLoading(false)
    }, 500)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <Navigation variant="dark" className="sticky top-0 z-10" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Welcome Back
          </h2>
          <p className="text-gray-400 text-lg">Your enterprise memory management at a glance</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <StatCard
                title="Total Memories"
                value={stats?.total_memories.toLocaleString() || '0'}
                icon="💾"
                trend="+12%"
                trendUp={true}
              />
              <StatCard
                title="Active Sessions"
                value={stats?.active_sessions.toString() || '0'}
                icon="⚡"
                trend="+5%"
                trendUp={true}
              />
              <StatCard
                title="Team Members"
                value={stats?.team_members.toString() || '0'}
                icon="👥"
                trend="2 new"
                trendUp={true}
              />
              <StatCard
                title="Storage Used"
                value={`${((stats?.storage_used_mb || 0) / 1024).toFixed(1)} GB`}
                icon="📊"
                trend="20% of limit"
                trendUp={false}
              />
              <StatCard
                title="API Calls Today"
                value={stats?.api_calls_today.toLocaleString() || '0'}
                icon="🔄"
                trend="+8%"
                trendUp={true}
              />
              <StatCard
                title="Plan"
                value="Pro"
                icon="⭐"
                trend="Upgrade available"
                trendUp={false}
              />
            </div>

            {/* Recent Activity */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">Recent Activity</h3>
              <div className="space-y-3">
                <ActivityItem
                  action="Memory created"
                  details="Project Alpha - Q4 Planning"
                  time="2 minutes ago"
                />
                <ActivityItem
                  action="Team member added"
                  details="john@example.com joined your team"
                  time="1 hour ago"
                />
                <ActivityItem
                  action="API integration"
                  details="Connected to Slack workspace"
                  time="3 hours ago"
                />
              </div>
            </div>
          </>
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
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700/50 shadow-xl hover:shadow-2xl transition-all hover:scale-105">
      <div className="flex items-start justify-between mb-4">
        <p className="text-gray-400 text-sm font-medium">{title}</p>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-white mb-2">{value}</p>
      <p className={`text-sm ${trendUp ? 'text-green-400' : 'text-gray-400'}`}>
        {trend}
      </p>
    </div>
  )
}

function ActivityItem({ action, details, time }: {
  action: string
  details: string
  time: string
}) {
  return (
    <div className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-700/30 transition">
      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
      <div className="flex-1">
        <p className="text-white font-medium">{action}</p>
        <p className="text-gray-400 text-sm">{details}</p>
      </div>
      <span className="text-gray-500 text-xs">{time}</span>
    </div>
  )
}
