// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';
import { cn } from '../../lib/utils';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Current progress value */
  value?: number;
  /** Maximum value (default: 100) */
  max?: number;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Color variant */
  variant?: 'primary' | 'success' | 'warning' | 'danger';
  /** Show percentage label */
  showLabel?: boolean;
  /** Additional CSS classes */
  className?: string;
}

const sizeStyles = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-4',
};

const variantStyles = {
  primary: 'bg-blue-600',
  success: 'bg-green-600',
  warning: 'bg-yellow-600',
  danger: 'bg-red-600',
};

/**
 * Progress component for displaying progress indicators
 *
 * @example
 * ```tsx
 * <Progress value={65} showLabel />
 * ```
 */
export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({
    className,
    value = 0,
    max = 100,
    size = 'md',
    variant = 'primary',
    showLabel = false,
    ...props
  }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
      <div className="w-full">
        <div
          ref={ref}
          className={cn(
            'relative w-full overflow-hidden rounded-full bg-gray-200',
            sizeStyles[size],
            className
          )}
          {...props}
        >
          <div
            className={cn(
              'h-full transition-all duration-300',
              variantStyles[variant]
            )}
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={value}
            aria-valuemin={0}
            aria-valuemax={max}
          />
        </div>
        {showLabel && (
          <p className="mt-1 text-sm text-gray-600 text-right">
            {Math.round(percentage)}%
          </p>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';
