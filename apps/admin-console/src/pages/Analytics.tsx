import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import adminApi from '../services/api'

interface PlatformMetrics {
  total_users: number
  total_teams: number
  active_users_30d: number
  active_teams_30d: number
  new_signups_30d: number
  new_teams_30d: number
  total_revenue_30d: number
  avg_team_size: number
  churn_rate: number
  platform_health_score: number
}

export default function Analytics() {
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const data = await adminApi.getPlatformMetrics()
        setMetrics(data)
        setLoading(false)
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
        setError('Failed to load analytics data. Using mock data.')
        // Fallback to mock data
        setMetrics({
          total_users: 2847,
          total_teams: 634,
          active_users_30d: 1892,
          active_teams_30d: 512,
          new_signups_30d: 342,
          new_teams_30d: 89,
          total_revenue_30d: 28450,
          avg_team_size: 4.2,
          churn_rate: 0.035,
          platform_health_score: 87.5,
        })
        setLoading(false)
      }
    }
    fetchMetrics()
  }, [])

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Nina Admin Console</h1>
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
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Platform Analytics</h2>
          <p className="text-gray-400">Real-time insights and business intelligence</p>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Total Users"
                value={metrics?.total_users.toLocaleString() || '0'}
                change="+12%"
                trend="up"
              />
              <MetricCard
                title="Active Teams"
                value={metrics?.total_teams.toLocaleString() || '0'}
                change="+8%"
                trend="up"
              />
              <MetricCard
                title="MRR"
                value={`$${(metrics?.total_revenue_30d || 0).toLocaleString()}`}
                change="+23%"
                trend="up"
              />
              <MetricCard
                title="Churn Rate"
                value={`${((metrics?.churn_rate || 0) * 100).toFixed(1)}%`}
                change="-0.5%"
                trend="down"
              />
            </div>

            {/* Additional Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Platform Health</h3>
                <div className="flex items-end space-x-2">
                  <span className="text-3xl font-bold text-green-400">
                    {metrics?.platform_health_score.toFixed(1)}
                  </span>
                  <span className="text-gray-400 mb-1">/100</span>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">New Signups (30d)</h3>
                <span className="text-3xl font-bold text-white">
                  {metrics?.new_signups_30d.toLocaleString()}
                </span>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Avg Team Size</h3>
                <span className="text-3xl font-bold text-white">
                  {metrics?.avg_team_size.toFixed(1)}
                </span>
              </div>
            </div>
          </>
        )}

        {/* Charts Placeholder */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">User Growth</h3>
            <div className="h-64 flex items-center justify-center text-gray-500">
              Chart: User growth over time
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Revenue Trends</h3>
            <div className="h-64 flex items-center justify-center text-gray-500">
              Chart: Revenue trends
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function MetricCard({ title, value, change, trend }: { title: string; value: string; change: string; trend: 'up' | 'down' }) {
  const trendColor = trend === 'up' ? 'text-green-400' : 'text-red-400'

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-3xl font-bold text-white mb-2">{value}</p>
      <p className={`text-sm ${trendColor}`}>{change} from last month</p>
    </div>
  )
}
