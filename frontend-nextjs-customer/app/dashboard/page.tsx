'use client';

import { Button, Card } from '@ninaivalaigal/ui-components';

export default function DashboardPage() {
  const handleNewMemory = () => {
    console.log('Create new memory');
    // TODO: Navigate to memory creation page
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <Button onClick={handleNewMemory} size="sm">
                New Memory
              </Button>
              <div className="h-8 w-8 rounded-full bg-gray-300" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">
              Total Memories
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">This Week</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">Categories</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">Shared</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">0</div>
          </Card>
        </div>

        {/* Recent Memories */}
        <Card className="bg-white" title="Recent Memories">
          <div className="text-center text-gray-500">
            <p className="text-sm">No memories yet</p>
            <p className="mt-1 text-xs">Create your first memory to get started</p>
            <div className="mt-4">
              <Button onClick={handleNewMemory} variant="secondary" size="sm">
                Create First Memory
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}
