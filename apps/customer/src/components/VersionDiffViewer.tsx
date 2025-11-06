// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#345: SPEC-035: Version Diff Visualization (SPEC-035)
 *
 * Component for visualizing differences between memory versions.
 * Shows side-by-side comparison with line-by-line diffs, highlighting additions, deletions, and changes.
 */

import { useState, useEffect } from 'react';
import type { AxiosError } from 'axios';
import apiClient from '../lib/apiClient';

export interface VersionDiff {
  version1: {
    id: string;
    version: number;
    content: string;
    created_at: string;
  };
  version2: {
    id: string;
    version: number;
    content: string;
    created_at: string;
  };
  changes: {
    type: 'added' | 'deleted' | 'modified' | 'unchanged';
    line: string;
    lineNumber: number;
    oldLineNumber?: number;
    newLineNumber?: number;
  }[];
  summary: {
    additions: number;
    deletions: number;
    modifications: number;
    unchanged: number;
  };
}

interface VersionDiffViewerProps {
  memoryId: string;
  version1: number;
  version2: number;
  onClose?: () => void;
}

export function VersionDiffViewer({ memoryId, version1, version2, onClose }: VersionDiffViewerProps) {
  const [diff, setDiff] = useState<VersionDiff | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side');

  useEffect(() => {
    loadDiff();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [memoryId, version1, version2]);

  const loadDiff = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<VersionDiff>(
        `/api/v1/memory/${memoryId}/versions/${version1}/diff/${version2}`
      );
      setDiff(response.data);
      setError(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load version diff');
    } finally {
      setLoading(false);
    }
  };

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'added':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'deleted':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'modified':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'added':
        return '+';
      case 'deleted':
        return '-';
      case 'modified':
        return '~';
      default:
        return ' ';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        {error}
      </div>
    );
  }

  if (!diff) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Version Comparison</h3>
          <p className="text-sm text-slate-400">
            Comparing version {diff.version1.version} → {diff.version2.version}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 border border-white/10 rounded-lg p-1">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-3 py-1 rounded text-sm font-medium transition-all duration-300 ${
                viewMode === 'side-by-side'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`px-3 py-1 rounded text-sm font-medium transition-all duration-300 ${
                viewMode === 'unified'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              Unified
            </button>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 border border-white/20 text-white rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-300"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <div className="text-sm text-emerald-300 mb-1">Additions</div>
          <div className="text-2xl font-bold text-white">{diff.summary.additions}</div>
        </div>
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4">
          <div className="text-sm text-rose-300 mb-1">Deletions</div>
          <div className="text-2xl font-bold text-white">{diff.summary.deletions}</div>
        </div>
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
          <div className="text-sm text-yellow-300 mb-1">Modifications</div>
          <div className="text-2xl font-bold text-white">{diff.summary.modifications}</div>
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-sm text-slate-400 mb-1">Unchanged</div>
          <div className="text-2xl font-bold text-white">{diff.summary.unchanged}</div>
        </div>
      </div>

      {/* Diff Content */}
      {viewMode === 'side-by-side' ? (
        <div className="grid grid-cols-2 gap-4 rounded-xl border border-white/10 bg-white/5 p-4">
          {/* Version 1 */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">
                Version {diff.version1.version}
              </h4>
              <span className="text-xs text-slate-400">
                {new Date(diff.version1.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 overflow-hidden">
              <div className="max-h-96 overflow-y-auto">
                {diff.changes.map((change, idx) => {
                  if (change.type === 'added') return null;
                  return (
                    <div
                      key={idx}
                      className={`px-4 py-2 border-l-4 ${getChangeColor(change.type)}`}
                    >
                      <div className="flex items-start space-x-2">
                        <span className="text-xs font-mono text-slate-500 w-8 flex-shrink-0">
                          {change.oldLineNumber || '-'}
                        </span>
                        <span className="text-xs font-mono w-4 flex-shrink-0">
                          {getChangeIcon(change.type)}
                        </span>
                        <span className="text-sm flex-1 font-mono whitespace-pre-wrap break-words">
                          {change.line}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Version 2 */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">
                Version {diff.version2.version}
              </h4>
              <span className="text-xs text-slate-400">
                {new Date(diff.version2.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 overflow-hidden">
              <div className="max-h-96 overflow-y-auto">
                {diff.changes.map((change, idx) => {
                  if (change.type === 'deleted') return null;
                  return (
                    <div
                      key={idx}
                      className={`px-4 py-2 border-l-4 ${getChangeColor(change.type)}`}
                    >
                      <div className="flex items-start space-x-2">
                        <span className="text-xs font-mono text-slate-500 w-8 flex-shrink-0">
                          {change.newLineNumber || '-'}
                        </span>
                        <span className="text-xs font-mono w-4 flex-shrink-0">
                          {getChangeIcon(change.type)}
                        </span>
                        <span className="text-sm flex-1 font-mono whitespace-pre-wrap break-words">
                          {change.line}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <div className="rounded-lg border border-slate-700 bg-slate-900/70 overflow-hidden">
            <div className="max-h-96 overflow-y-auto">
              {diff.changes.map((change, idx) => (
                <div
                  key={idx}
                  className={`px-4 py-2 border-l-4 ${getChangeColor(change.type)}`}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-xs font-mono text-slate-500 w-12 flex-shrink-0">
                      {change.oldLineNumber || '-'}
                    </span>
                    <span className="text-xs font-mono text-slate-500 w-12 flex-shrink-0">
                      {change.newLineNumber || '-'}
                    </span>
                    <span className="text-xs font-mono w-4 flex-shrink-0">
                      {getChangeIcon(change.type)}
                    </span>
                    <span className="text-sm flex-1 font-mono whitespace-pre-wrap break-words">
                      {change.line}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
