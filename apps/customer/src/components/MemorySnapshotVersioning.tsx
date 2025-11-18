// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#346: Memory Snapshot Versioning UI Components (SPEC-035)
 *
 * Components for creating, viewing, and restoring memory snapshots.
 * Supports version history, diff visualization, and rollback.
 */

import { useState, useEffect } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';
import { VersionDiffViewer } from './VersionDiffViewer';

export interface MemorySnapshot {
  id: string;
  memory_id: string;
  version: number;
  name: string;
  description: string | null;
  created_at: string;
  created_by: string;
  memory_count: number;
  snapshot_size_bytes: number;
}

interface MemorySnapshotVersioningProps {
  memoryId: string;
  onSnapshotCreated?: (snapshot: MemorySnapshot) => void;
  onSnapshotRestored?: (snapshotId: string) => void;
}

export function MemorySnapshotVersioning({ memoryId, onSnapshotCreated, onSnapshotRestored }: MemorySnapshotVersioningProps) {
  const [snapshots, setSnapshots] = useState<MemorySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState<string | null>(null);
  const [diffView, setDiffView] = useState<{ version1: number; version2: number } | null>(null);

  const [snapshotName, setSnapshotName] = useState('');
  const [snapshotDescription, setSnapshotDescription] = useState('');

  useEffect(() => {
    loadSnapshots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [memoryId]);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<MemorySnapshot[]>(
        `/api/v1/memories/versions/${memoryId}/snapshots`
      );
      setSnapshots(Array.isArray(response.data) ? response.data : []);
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load snapshots');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSnapshot = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);

    try {
      // First get current memory content
      const memoryResponse = await apiClient.get(`/api/v1/memories/${memoryId}`);
      const memory = memoryResponse.data;

      const response = await apiClient.post<{ snapshot: { snapshot: MemorySnapshot }; message: string }>(
        `/api/v1/memories/versions/snapshots`,
        {
          memory_id: memoryId,
          content: memory.content || '',
          metadata: memory.metadata || {},
          snapshot_label: snapshotName,
        }
      );

      const newSnapshot: MemorySnapshot = {
        id: response.data.snapshot.snapshot.id,
        memory_id: memoryId,
        version: response.data.snapshot.snapshot.version,
        name: response.data.snapshot.snapshot.name,
        description: response.data.snapshot.snapshot.description,
        created_at: response.data.snapshot.snapshot.created_at,
        created_by: 'current-user', // This should come from the API
        memory_count: 0, // This should come from the API
        snapshot_size_bytes: 0, // This should come from the API
      };
      setSnapshots([newSnapshot, ...snapshots]);
      setSnapshotName('');
      setSnapshotDescription('');
      setShowCreateForm(false);
      onSnapshotCreated?.(newSnapshot);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to create snapshot');
    } finally {
      setCreating(false);
    }
  };

  const handleRestoreSnapshot = async (snapshotId: string) => {
    if (!confirm('Are you sure you want to restore this snapshot? This will overwrite current memory state.')) {
      return;
    }

    setRestoring(snapshotId);
    try {
      await apiClient.post(`/api/v1/memories/versions/${memoryId}/restore`, {
        version_id: snapshotId,
        restore_notes: `Restored snapshot: ${snapshotName || 'Unlabeled'}`,
      });
      onSnapshotRestored?.(snapshotId);
      alert('Snapshot restored successfully');
      // Reload snapshots to get updated version numbers
      loadSnapshots();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      alert(axiosError.response?.data?.detail || axiosError.message || 'Failed to restore snapshot');
    } finally {
      setRestoring(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Memory Snapshots</h3>
          <p className="text-sm text-slate-400">Create and restore memory state snapshots</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105"
        >
          {showCreateForm ? 'Cancel' : '+ Create Snapshot'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {/* Create Snapshot Form */}
      {showCreateForm && (
        <form onSubmit={handleCreateSnapshot} className="rounded-xl border border-white/10 bg-white/5 p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Snapshot Name *
            </label>
            <input
              type="text"
              value={snapshotName}
              onChange={(e) => setSnapshotName(e.target.value)}
              required
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              placeholder="e.g., Pre-migration snapshot"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Description
            </label>
            <textarea
              value={snapshotDescription}
              onChange={(e) => setSnapshotDescription(e.target.value)}
              rows={3}
              className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
              placeholder="Optional description of this snapshot"
            />
          </div>
          <div className="flex items-center space-x-3">
            <button
              type="submit"
              disabled={creating || !snapshotName.trim()}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? 'Creating...' : 'Create Snapshot'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(false);
                setSnapshotName('');
                setSnapshotDescription('');
              }}
              className="px-4 py-2 border border-white/20 text-white rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-300"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Snapshots List */}
      {snapshots.length === 0 ? (
        <div className="text-center py-12 rounded-xl border border-white/10 bg-white/5">
          <div className="text-4xl mb-3">📸</div>
          <p className="text-slate-400">No snapshots yet</p>
          <p className="text-sm text-slate-500 mt-1">Create your first snapshot to save memory state</p>
        </div>
      ) : (
        <div className="space-y-3">
          {snapshots.map((snapshot) => (
            <div
              key={snapshot.id}
              className="rounded-xl border border-white/10 bg-white/5 p-5 hover:bg-white/10 transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-base font-semibold text-white">{snapshot.name}</h4>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-medium">
                      v{snapshot.version}
                    </span>
                  </div>
                  {snapshot.description && (
                    <p className="text-sm text-slate-400 mb-3">{snapshot.description}</p>
                  )}
                  <div className="flex items-center space-x-4 text-xs text-slate-500">
                    <span>📊 {snapshot.memory_count} memories</span>
                    <span>💾 {formatSize(snapshot.snapshot_size_bytes)}</span>
                    <span>🕒 {formatDate(snapshot.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  {snapshots.length > 1 && snapshot.version > 1 && (
                    <button
                      onClick={() => {
                        const prevSnapshot = snapshots.find(s => s.version === snapshot.version - 1);
                        if (prevSnapshot) {
                          setDiffView({ version1: prevSnapshot.version, version2: snapshot.version });
                        }
                      }}
                      className="px-3 py-1.5 border border-white/20 text-white rounded-lg text-xs font-medium hover:bg-white/10 transition-all duration-300"
                    >
                      View Diff
                    </button>
                  )}
                  <button
                    onClick={() => handleRestoreSnapshot(snapshot.id)}
                    disabled={restoring === snapshot.id}
                    className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg text-xs font-medium transition-all duration-300 disabled:opacity-50"
                  >
                    {restoring === snapshot.id ? 'Restoring...' : 'Restore'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Diff Viewer Modal */}
      {diffView && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-6xl rounded-xl border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 max-h-[90vh] overflow-y-auto">
            <VersionDiffViewer
              memoryId={memoryId}
              version1={diffView.version1}
              version2={diffView.version2}
              onClose={() => setDiffView(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
