import { Link } from 'react-router-dom'

export default function Teams() {
  const teams = [
    { id: '1', name: 'Acme Corp', members: 12, plan: 'Enterprise', status: 'Active', mrr: 500 },
    { id: '2', name: 'Tech Startup', members: 5, plan: 'Pro', status: 'Active', mrr: 29 },
    { id: '3', name: 'Design Agency', members: 8, plan: 'Pro', status: 'Trial', mrr: 0 },
  ]

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Nina Admin Console</h1>
            <nav className="flex space-x-4">
              <Link to="/analytics" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Analytics
              </Link>
              <Link to="/teams" className="text-blue-400 hover:text-blue-300 px-3 py-2 rounded-md text-sm font-medium">
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
          <h2 className="text-3xl font-bold text-white mb-2">Team Management</h2>
          <p className="text-gray-400">Monitor and manage all teams on the platform</p>
        </div>

        {/* Teams Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-750">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Team</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Members</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Plan</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">MRR</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {teams.map((team) => (
                <tr key={team.id} className="hover:bg-gray-750">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{team.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{team.members}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{team.plan}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      team.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {team.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${team.mrr}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-400 hover:text-blue-300 cursor-pointer">
                    View Details
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
