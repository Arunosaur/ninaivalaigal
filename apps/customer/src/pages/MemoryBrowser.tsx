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
import axios from 'axios';

const API_BASE_URL = (import.meta.env?.VITE_API_URL as string) || 'http://localhost:13390';

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
      const token = localStorage.getItem('auth_token');

      const response = await axios.get(`${API_BASE_URL}/api/v1/memory/memories`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const memoriesData = response.data.memories || response.data || [];
      setMemories(memoriesData);
      setFilteredMemories(memoriesData);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load memories:', err);
      setError(err.message || 'Failed to load memories');
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
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

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
        <div className="bg-white shadow-md rounded-lg p-6 mb-6">
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
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Search memories by content, tags, or context..."
                />
              </div>
            </div>

            {/* Filter Controls */}
            <div className="flex items-center space-x-3">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                className={`${
                  guidedMode ? 'bg-purple-700' : 'bg-purple-600 hover:bg-purple-700'
                } text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50`}
              >
                <span>📖</span>
                <span>{guidedMode ? 'Guided Mode Active' : 'Guided Mode'}</span>
              </button>

              <button
                onClick={loadMemories}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
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
                  <span className="text-sm text-gray-700">Pinned Only</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filterArchived}
                    onChange={(e) => setFilterArchived(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-700">Show Archived</span>
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
  const createdDate = new Date(memory.created_at).toLocaleDateString();
  const isRecent =
    (new Date().getTime() - new Date(memory.created_at).getTime()) / (1000 * 60 * 60 * 24) < 7;

  return (
    <div
      id={`memory-card-${memory.id}`}
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 p-4 cursor-pointer hover:-translate-y-1"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {memory.pinned && <span className="text-yellow-500">📌</span>}
          {memory.archived && <span className="text-gray-500">📦</span>}
          {isRecent && <span className="text-green-500">🆕</span>}
          <span className="text-xs text-gray-500">
            {(memory.relevance_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-xs text-gray-400">{memory.size} chars</span>
          <div
            className={`w-2 h-2 rounded-full ${
              memory.relevance_score > 0.9
                ? 'bg-green-500'
                : memory.relevance_score > 0.8
                ? 'bg-yellow-500'
                : 'bg-gray-400'
            }`}
          ></div>
        </div>
      </div>

      {/* Content */}
      <div className="text-gray-800 text-sm mb-4 line-clamp-4">{memory.content}</div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-3">
        {memory.tags.slice(0, 3).map((tag: string) => (
          <span
            key={tag}
            className="inline-block bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium"
          >
            {tag}
          </span>
        ))}
        {memory.tags.length > 3 && (
          <span className="inline-block bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs">
            +{memory.tags.length - 3} more
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{memory.context.replace(/-/g, ' ')}</span>
        <span>{createdDate}</span>
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
