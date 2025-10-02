import { Link } from 'react-router-dom'

export default function Analytics() {
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

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard title="Total Users" value="2,847" change="+12%" trend="up" />
          <MetricCard title="Active Teams" value="634" change="+8%" trend="up" />
          <MetricCard title="MRR" value="$28,450" change="+23%" trend="up" />
          <MetricCard title="Churn Rate" value="3.5%" change="-0.5%" trend="down" />
        </div>

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
