export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500">
                New Memory
              </button>
              <div className="h-8 w-8 rounded-full bg-gray-300" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg bg-white p-6 shadow">
            <div className="text-sm font-medium text-gray-500">
              Total Memories
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </div>
          <div className="rounded-lg bg-white p-6 shadow">
            <div className="text-sm font-medium text-gray-500">
              This Week
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </div>
          <div className="rounded-lg bg-white p-6 shadow">
            <div className="text-sm font-medium text-gray-500">
              Categories
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </div>
          <div className="rounded-lg bg-white p-6 shadow">
            <div className="text-sm font-medium text-gray-500">
              Shared
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </div>
        </div>

        {/* Recent Memories */}
        <div className="rounded-lg bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Memories
            </h2>
          </div>
          <div className="p-6">
            <div className="text-center text-gray-500">
              <p className="text-sm">No memories yet</p>
              <p className="mt-1 text-xs">
                Create your first memory to get started
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
