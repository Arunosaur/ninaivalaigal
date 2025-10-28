// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * SPEC-076: Memory Browser with Guided Tour
 *
 * Full React implementation of Memory Browser with integrated guided tour.
 */

import { useState, useEffect } from 'react';
import { GuidedTour, type Memory } from '@nina/ui';
import { Navigation } from '../components/Navigation';
import apiClient from '../lib/apiClient';
import '../styles/memory-browser.css';

export default function MemoryBrowser() {
  // State
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_desc');
  const [showFilters, setShowFilters] = useState(false);
  const [guidedMode, setGuidedMode] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [filterContext, setFilterContext] = useState('all');
  const [filterPinned, setFilterPinned] = useState(false);
  const [filterArchived, setFilterArchived] = useState(false);

  const PAGE_SIZE = 12;

  // Load memories from API
  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/memory/memories');

      const memoriesData = response.data.memories || response.data || [];
      setMemories(memoriesData);
      setFilteredMemories(memoriesData);
      setError(null);
    } catch (err: unknown) {
      const fallbackMessage =
        err instanceof Error ? err.message : 'Failed to load memories';
      setError(fallbackMessage);
      // Use sample data for development
      const sampleMemories = generateSampleMemories();
      setMemories(sampleMemories);
      setFilteredMemories(sampleMemories);
    } finally {
      setLoading(false);
    }
  };

  // Filter and search
  useEffect(() => {
    let filtered = [...memories];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (m) =>
          m.content.toLowerCase().includes(term) ||
          m.tags.some((tag: string) => tag.toLowerCase().includes(term)) ||
          m.context.toLowerCase().includes(term)
      );
    }

    // Context filter
    if (filterContext !== 'all') {
      filtered = filtered.filter((m) => m.context === filterContext);
    }

    // Pinned filter
    if (filterPinned) {
      filtered = filtered.filter((m) => m.pinned);
    }

    // Archived filter
    if (!filterArchived) {
      filtered = filtered.filter((m) => !m.archived);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'created_desc':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'created_asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'updated_desc':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'relevance':
          return b.relevance_score - a.relevance_score;
        case 'size_desc':
          return b.size - a.size;
        default:
          return 0;
      }
    });

    setFilteredMemories(filtered);
    setCurrentPage(1); // Reset to first page on filter change
  }, [searchTerm, sortBy, filterContext, filterPinned, filterArchived, memories]);

  // Pagination
  const totalPages = Math.ceil(filteredMemories.length / PAGE_SIZE);
  const paginatedMemories = filteredMemories.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  // Get unique contexts for filter
  const uniqueContexts = Array.from(new Set(memories.map((m) => m.context)));

  // Guided tour handlers
  const handleStartGuidedTour = () => {
    setGuidedMode(true);
  };

  const handleExitGuidedTour = () => {
    setGuidedMode(false);
  };

  const handleCompleteTour = () => {
    setGuidedMode(false);
    showNotification('✅ Tour completed!', 'success');
  };

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    // Simple notification (can be enhanced with a proper toast library)
    const notification = document.createElement('div');
    const bgColor =
      type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600';
    notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg ${bgColor} text-white transition-opacity duration-300`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading memories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Navigation */}
      <Navigation variant="dark" className="sticky top-0 z-10" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">
              ⚠️ API connection failed. Showing sample data for development.
            </p>
          </div>
        )}

        {/* Search and Filters */}
        <div className="card-shadow rounded-lg p-6 mb-6" style={{ background: 'rgba(31, 41, 55, 0.5)', backdropFilter: 'blur(10px)' }}>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Search Bar */}
            <div className="flex-1 max-w-2xl">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    ></path>
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-800 text-gray-100 placeholder-gray-400"
                  placeholder="Search memories by content, tags, or context..."
                />
              </div>
            </div>

            {/* Filter Controls */}
            <div className="flex items-center space-x-3">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-gray-800 text-gray-100"
              >
                <option value="created_desc">Newest First</option>
                <option value="created_asc">Oldest First</option>
                <option value="updated_desc">Recently Updated</option>
                <option value="relevance">Most Relevant</option>
                <option value="size_desc">Largest First</option>
              </select>

              <button
                onClick={() => setShowFilters(!showFilters)}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors"
              >
                🔍 Filters
              </button>

              {/* Guided Mode Toggle (SPEC-076) */}
              <button
                onClick={handleStartGuidedTour}
                disabled={guidedMode}
                className={`btn-primary flex items-center space-x-2 ${guidedMode ? 'opacity-75' : ''}`}
              >
                <span>📖</span>
                <span>{guidedMode ? 'Guided Mode Active' : 'Guided Mode'}</span>
              </button>

              <button
                onClick={loadMemories}
                className="btn-secondary"
              >
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Expanded Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Context</label>
                <select
                  value={filterContext}
                  onChange={(e) => setFilterContext(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Contexts</option>
                  {uniqueContexts.map((ctx) => (
                    <option key={ctx} value={ctx}>
                      {ctx.replace(/-/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end space-x-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filterPinned}
                    onChange={(e) => setFilterPinned(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-300">Pinned Only</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filterArchived}
                    onChange={(e) => setFilterArchived(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-300">Show Archived</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Memory Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          {paginatedMemories.map((memory) => (
            <MemoryCard key={memory.id} memory={memory} />
          ))}
        </div>

        {/* Empty State */}
        {filteredMemories.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No memories found</p>
            <p className="text-gray-400 mt-2">Try adjusting your search or filters</p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center space-x-4">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>
            <span className="text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      {/* Guided Tour Overlay */}
      {guidedMode && (
        <GuidedTour
          memories={filteredMemories.length > 0 ? filteredMemories : memories}
          isActive={guidedMode}
          onComplete={handleCompleteTour}
          onExit={handleExitGuidedTour}
        />
      )}
    </div>
  );
}

// Memory Card Component
interface MemoryCardProps {
  memory: Memory;
}

function MemoryCard({ memory }: MemoryCardProps) {
  return (
    <div id={`memory-card-${memory.id}`} className="memory-card">
      <div className="memory-card-header">
        <div className="flex items-center justify-between mb-3">
          <span className={`context-badge ${memory.context.toLowerCase()}`}>
            {memory.context}
          </span>
          <div className="flex items-center space-x-2">
            {memory.pinned && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-medium">
                📌 Pinned
              </span>
            )}
            {memory.archived && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium">
                📦 Archived
              </span>
            )}
          </div>
        </div>
        <h3 className="text-lg font-bold text-gray-100 leading-tight">
          {memory.content.substring(0, 100)}
          {memory.content.length > 100 && '...'}
        </h3>
      </div>

      <div className="memory-card-body">
        <div className="memory-content text-gray-300 mb-4">
          {memory.content}
        </div>

        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {memory.tags.map((tag, idx) => (
              <span key={idx} className="tag">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="memory-card-footer flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {new Date(memory.created_at).toLocaleDateString()}
          </span>
          {memory.size && (
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {(memory.size / 1024).toFixed(1)} KB
            </span>
          )}
        </div>
        <button
          onClick={() => alert(`Memory ID: ${memory.id}\n\nContent: ${memory.content}\n\nContext: ${memory.context}\n\nTags: ${memory.tags.join(', ')}\n\nCreated: ${new Date(memory.created_at).toLocaleString()}`)}
          className="text-purple-400 hover:text-purple-300 font-medium transition-colors"
        >
          View Details →
        </button>
      </div>
    </div>
  );
}

// Sample data generator for development
function generateSampleMemories(): Memory[] {
  const contexts = ['work', 'personal', 'learning', 'ideas'];
  const tags = ['important', 'todo', 'reference', 'project', 'meeting', 'research'];

  return Array.from({ length: 20 }, (_, i) => ({
    id: `mem-${i + 1}`,
    content: `Sample memory content ${i + 1}. This is a placeholder memory for development and testing purposes.`,
    context: contexts[i % contexts.length],
    tags: [tags[i % tags.length], tags[(i + 1) % tags.length]],
    created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - i * 12 * 60 * 60 * 1000).toISOString(),
    pinned: i % 5 === 0,
    archived: i % 10 === 0,
    relevance_score: 0.5 + Math.random() * 0.5,
    size: 100 + Math.floor(Math.random() * 400),
  }));
}
