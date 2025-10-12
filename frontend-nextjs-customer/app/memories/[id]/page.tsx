// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@ninaivalaigal/ui-components';
import { useMemories } from '../../../hooks/useMemories';
import { CreateMemoryModal } from '../../../components/CreateMemoryModal';
import type { Memory } from '../../../types/api';

interface MemoryDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function MemoryDetailPage({ params }: MemoryDetailPageProps) {
  const router = useRouter();
  const { memories, isLoading, deleteMemory } = useMemories();
  const [resolvedParams, setResolvedParams] = useState<{ id: string } | null>(null);
  const [memory, setMemory] = useState<Memory | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Resolve params promise
  useEffect(() => {
    params.then(setResolvedParams);
  }, [params]);

  // Find the memory by ID
  useEffect(() => {
    if (resolvedParams && memories.length > 0) {
      const foundMemory = memories.find(m => m.id === resolvedParams.id);
      setMemory(foundMemory || null);
    }
  }, [resolvedParams, memories]);

  const handleDelete = async () => {
    if (!memory) return;

    const confirmed = window.confirm(
      'Are you sure you want to delete this memory? This action cannot be undone.'
    );

    if (!confirmed) return;

    setIsDeleting(true);
    const { success } = await deleteMemory(memory.id);

    if (success) {
      router.push('/memories');
    } else {
      setIsDeleting(false);
      alert('Failed to delete memory. Please try again.');
    }
  };

  const handleShare = () => {
    // TODO: Implement share functionality
    alert('Share functionality coming soon!');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 w-48 bg-gray-200 rounded mb-4"></div>
            <div className="h-64 bg-white rounded-lg shadow"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!memory) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Memory Not Found</h2>
            <p className="text-gray-600 mb-6">
              The memory you're looking for doesn't exist or has been deleted.
            </p>
            <Button onClick={() => router.push('/memories')}>
              Back to Memories
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const categoryColors = {
    personal: 'bg-blue-100 text-blue-800',
    work: 'bg-purple-100 text-purple-800',
    shared: 'bg-green-100 text-green-800',
  };

  const categoryColor = memory.category
    ? categoryColors[memory.category as keyof typeof categoryColors]
    : 'bg-gray-100 text-gray-800';

  return (
    <>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          {/* Breadcrumb Navigation */}
          <nav className="mb-6 flex items-center text-sm text-gray-500">
            <button
              onClick={() => router.push('/dashboard')}
              className="hover:text-gray-700 transition-colors"
            >
              Dashboard
            </button>
            <span className="mx-2">/</span>
            <button
              onClick={() => router.push('/memories')}
              className="hover:text-gray-700 transition-colors"
            >
              Memories
            </button>
            <span className="mx-2">/</span>
            <span className="text-gray-900 font-medium">
              {memory.title || 'Memory Detail'}
            </span>
          </nav>

          {/* Memory Header */}
          <div className="bg-white rounded-lg shadow-sm mb-6">
            <div className="px-6 py-8">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  {memory.title && (
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                      {memory.title}
                    </h1>
                  )}
                  <div className="flex items-center gap-3 flex-wrap">
                    {memory.category && (
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${categoryColor}`}>
                        {memory.category}
                      </span>
                    )}
                    <span className="text-sm text-gray-500">
                      Created {new Date(memory.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                    {memory.updated_at && memory.updated_at !== memory.created_at && (
                      <span className="text-sm text-gray-500">
                        • Updated {new Date(memory.updated_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant="secondary"
                    onClick={handleShare}
                    className="whitespace-nowrap"
                  >
                    Share
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setIsEditModalOpen(true)}
                    className="whitespace-nowrap"
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    onClick={handleDelete}
                    isLoading={isDeleting}
                    className="whitespace-nowrap"
                  >
                    Delete
                  </Button>
                </div>
              </div>

              {/* Tags */}
              {memory.tags && memory.tags.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap mb-6">
                  <span className="text-sm text-gray-500">Tags:</span>
                  {memory.tags.map((tag: string, index: number) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Content */}
              <div className="prose prose-sm max-w-none">
                <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {memory.content}
                </div>
              </div>
            </div>
          </div>

          {/* Metadata Card */}
          <div className="bg-white rounded-lg shadow-sm mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Metadata</h2>
            </div>
            <div className="px-6 py-4">
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Memory ID</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">{memory.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">User ID</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">{memory.user_id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Created At</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(memory.created_at).toLocaleString('en-US', {
                      dateStyle: 'full',
                      timeStyle: 'short',
                    })}
                  </dd>
                </div>
                {memory.updated_at && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Date(memory.updated_at).toLocaleString('en-US', {
                        dateStyle: 'full',
                        timeStyle: 'short',
                      })}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Related Memories Section (Placeholder) */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Related Memories</h2>
            </div>
            <div className="px-6 py-8">
              <div className="text-center text-gray-500">
                <div className="text-4xl mb-2">🔗</div>
                <p className="text-sm">Related memories will appear here</p>
                <p className="text-xs text-gray-400 mt-1">Feature coming soon</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <CreateMemoryModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
      />
    </>
  );
}
