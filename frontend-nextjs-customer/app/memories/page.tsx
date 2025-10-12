// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, useDebounce } from '@ninaivalaigal/ui-components';
import { CreateMemoryModal } from '../../components/CreateMemoryModal';
import { MemoryCard } from '../../components/MemoryCard';
import { useMemories } from '../../hooks/useMemories';

type FilterType = 'all' | 'personal' | 'work' | 'shared';

export default function MemoriesPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const debouncedSearch = useDebounce(searchQuery, 300);

  const { memories, isLoading } = useMemories();

  const handleNewMemory = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleMemoryClick = (id: string) => {
    router.push(`/memories/${id}`);
  };

  const handleMemoryShare = (id: string) => {
    console.log('Share memory:', id);
    // TODO: Implement share functionality
  };

  const handleMemoryEdit = (id: string) => {
    console.log('Edit memory:', id);
    // TODO: Implement edit functionality
  };

  // Filter and search memories
  const filteredMemories = useMemo(() => {
    let filtered = memories;

    // Apply category filter
    if (activeFilter !== 'all') {
      filtered = filtered.filter(m => m.category === activeFilter);
    }

    // Apply search filter
    if (debouncedSearch.trim()) {
      const searchLower = debouncedSearch.toLowerCase();
      filtered = filtered.filter(m =>
        m.content.toLowerCase().includes(searchLower) ||
        m.title?.toLowerCase().includes(searchLower) ||
        m.tags?.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    return filtered;
  }, [memories, activeFilter, debouncedSearch]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">My Memories</h1>
            <div className="flex items-center space-x-4">
              <div className="relative w-64">
                <Input
                  type="search"
                  placeholder="Search memories..."
                  value={searchQuery}
                  onChange={handleSearch}
                    variant="default"
                />
              </div>
              <Button onClick={handleNewMemory} size="sm">
                New Memory
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="mb-6 flex items-center space-x-4">
          <Button
            variant={activeFilter === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveFilter('all')}
          >
            All
          </Button>
          <Button
            variant={activeFilter === 'personal' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveFilter('personal')}
          >
            Personal
          </Button>
          <Button
            variant={activeFilter === 'work' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveFilter('work')}
          >
            Work
          </Button>
          <Button
            variant={activeFilter === 'shared' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveFilter('shared')}
          >
            Shared
          </Button>
        </div>

        {/* Memories Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            // Loading State
            <div className="col-span-full text-center py-12">
              <p className="text-gray-500">Loading memories...</p>
            </div>
          ) : filteredMemories.length === 0 ? (
            // Empty State
            <div className="col-span-full rounded-lg border-2 border-dashed border-gray-300 bg-white p-12 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-semibold text-gray-900">
                {searchQuery || activeFilter !== 'all' ? 'No matching memories' : 'No memories'}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery || activeFilter !== 'all'
                  ? 'Try adjusting your filters or search query.'
                  : 'Get started by creating a new memory.'}
              </p>
              {!searchQuery && activeFilter === 'all' && (
                <div className="mt-6">
                  <Button onClick={handleNewMemory} size="sm">
                    <svg
                      className="-ml-0.5 mr-1.5 h-5 w-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    New Memory
                  </Button>
                </div>
              )}
            </div>
          ) : (
            // Memory Cards
            filteredMemories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                onClick={() => handleMemoryClick(memory.id)}
                onShare={() => handleMemoryShare(memory.id)}
                onEdit={() => handleMemoryEdit(memory.id)}
              />
            ))
          )}
        </div>
      </main>

      {/* Create Memory Modal */}
      <CreateMemoryModal isOpen={isCreateModalOpen} onClose={handleCloseModal} />
    </div>
  );
}
