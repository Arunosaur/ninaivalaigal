// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { Badge, Card } from '@ninaivalaigal/ui-components';
import type { Memory } from '../types/api';

type MemoryCardProps = {
  memory: Memory;
  onClick?: (memory: Memory) => void;
  onShare?: (id: string) => void;
  onEdit?: (id: string) => void;
};

export function MemoryCard({ memory, onClick, onShare, onEdit }: MemoryCardProps) {
  const categoryVariants = {
    personal: 'info',
    work: 'accent',
    shared: 'success',
  } as const;

  const handleClick = () => {
    onClick?.(memory);
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    onShare?.(memory.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(memory.id);
  };

  return (
    <Card
      className="cursor-pointer bg-white transition-shadow hover:shadow-lg"
      onClick={handleClick}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <h3 className="line-clamp-2 text-lg font-semibold text-gray-900">
            {memory.title || 'Untitled Memory'}
          </h3>
          {memory.category && (
            <Badge
              className="ml-2 flex-shrink-0"
              variant={categoryVariants[memory.category] ?? 'neutral'}
              pill
            >
              {memory.category}
            </Badge>
          )}
        </div>

        {/* Content Preview */}
        <p className="line-clamp-3 text-sm text-gray-600">{memory.content}</p>

        {/* Tags */}
        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {memory.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="neutral">
                #{tag}
              </Badge>
            ))}
            {memory.tags.length > 3 && (
              <Badge variant="neutral">+{memory.tags.length - 3}</Badge>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-100 pt-3 text-xs text-gray-500">
          <span>{new Date(memory.created_at).toLocaleDateString()}</span>
          <div className="flex items-center space-x-2">
            <button
              className="text-gray-400 hover:text-gray-600"
              onClick={handleShare}
              title="Share memory"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
            </button>
            <button
              className="text-gray-400 hover:text-gray-600"
              onClick={handleEdit}
              title="Edit memory"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}
