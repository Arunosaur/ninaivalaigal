// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';
import { cn } from '../../lib/utils';

export interface AchievementBadge {
  id: string;
  title: string;
  description: string;
  icon: string;
  level: 'bronze' | 'silver' | 'gold' | 'platinum';
}

export interface AchievementProps {
  /** Achievement badge data */
  badge: AchievementBadge;
  /** Date earned */
  earnedAt?: string;
  /** Progress percentage (0-100) */
  progress?: number;
  /** Click handler */
  onClick?: () => void;
  /** Additional CSS classes */
  className?: string;
}

const levelColors = {
  bronze: 'border-amber-300 bg-amber-50 text-amber-900',
  silver: 'border-gray-300 bg-gray-50 text-gray-900',
  gold: 'border-yellow-300 bg-yellow-50 text-yellow-900',
  platinum: 'border-purple-300 bg-purple-50 text-purple-900',
};

/**
 * Achievement component for displaying user badges and progress
 *
 * @example
 * ```tsx
 * <Achievement
 *   badge={{
 *     id: '1',
 *     title: 'First Memory',
 *     description: 'Created your first memory',
 *     icon: '🎉',
 *     level: 'bronze'
 *   }}
 *   earnedAt="2025-01-15"
 *   progress={100}
 * />
 * ```
 */
export const Achievement: React.FC<AchievementProps> = ({
  badge,
  earnedAt,
  progress,
  onClick,
  className,
}) => {
  const isEarned = progress === 100 || earnedAt;

  return (
    <div
      className={cn(
        'rounded-lg border-2 p-4 transition-all',
        isEarned ? levelColors[badge.level] : 'border-gray-200 bg-gray-50 opacity-60',
        onClick && 'cursor-pointer hover:shadow-md',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="text-3xl">{badge.icon}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm mb-1">{badge.title}</h4>
          <p className="text-xs text-gray-600 mb-2">{badge.description}</p>

          {progress !== undefined && progress < 100 && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Progress</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {earnedAt && (
            <div className="text-xs text-gray-500 mt-2">
              Earned {new Date(earnedAt).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
