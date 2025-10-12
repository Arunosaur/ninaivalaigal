// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState } from 'react';
import { Button, Card } from '@ninaivalaigal/ui-components';
import { CreateMemoryModal } from '../../components/CreateMemoryModal';
import { useMemories } from '../../hooks/useMemories';

export default function DashboardPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { memories, isLoading } = useMemories();

  const handleNewMemory = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
  };

  // Calculate stats from memories
  const totalMemories = memories.length;
  const thisWeekMemories = memories.filter(m => {
    const memoryDate = new Date(m.created_at);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return memoryDate >= weekAgo;
  }).length;
  const categories = new Set(memories.map(m => m.category).filter(Boolean)).size;
  const sharedMemories = memories.filter(m => m.category === 'shared').length;

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
            <div className="mt-2 text-3xl font-bold text-gray-900">
              {isLoading ? '...' : totalMemories}
            </div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">This Week</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">
              {isLoading ? '...' : thisWeekMemories}
            </div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">Categories</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">
              {isLoading ? '...' : categories}
            </div>
          </Card>
          <Card className="bg-white">
            <div className="text-sm font-medium text-gray-500">Shared</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">
              {isLoading ? '...' : sharedMemories}
            </div>
          </Card>
        </div>

        {/* Recent Memories */}
        <Card className="bg-white" title="Recent Memories">
          {isLoading ? (
            <div className="text-center text-gray-500">
              <p className="text-sm">Loading memories...</p>
            </div>
          ) : memories.length === 0 ? (
            <div className="text-center text-gray-500">
              <p className="text-sm">No memories yet</p>
              <p className="mt-1 text-xs">Create your first memory to get started</p>
              <div className="mt-4">
                <Button onClick={handleNewMemory} variant="secondary" size="sm">
                  Create First Memory
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {memories.slice(0, 5).map((memory) => (
                <div
                  key={memory.id}
                  className="border-b border-gray-100 pb-4 last:border-0 last:pb-0"
                >
                  <h3 className="font-medium text-gray-900">
                    {memory.title || 'Untitled Memory'}
                  </h3>
                  <p className="mt-1 line-clamp-2 text-sm text-gray-600">
                    {memory.content}
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                    {memory.category && (
                      <span className="rounded-full bg-blue-100 px-2 py-1 text-blue-700">
                        {memory.category}
                      </span>
                    )}
                    <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>

      {/* Create Memory Modal */}
      <CreateMemoryModal isOpen={isCreateModalOpen} onClose={handleCloseModal} />
    </div>
  );
}
