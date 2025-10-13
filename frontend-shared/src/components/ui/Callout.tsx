// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';
import { cn } from '../../lib/utils';

export interface CalloutProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual variant */
  variant?: 'info' | 'warning' | 'error' | 'success';
  /** Callout title */
  title?: string;
  /** Additional CSS classes */
  className?: string;
  /** Child content */
  children: React.ReactNode;
}

const variantStyles = {
  info: 'border-blue-200 bg-blue-50 text-blue-900',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  success: 'border-green-200 bg-green-50 text-green-900',
};

const iconMap = {
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌',
  success: '✅',
};

/**
 * Callout component for highlighted notices and alerts
 *
 * @example
 * ```tsx
 * <Callout variant="warning" title="Important">
 *   Please review before proceeding
 * </Callout>
 * ```
 */
export const Callout = React.forwardRef<HTMLDivElement, CalloutProps>(
  ({ variant = 'info', title, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-lg border p-4',
          variantStyles[variant],
          className
        )}
        role="alert"
        {...props}
      >
        <div className="flex gap-3">
          <span className="text-xl flex-shrink-0">{iconMap[variant]}</span>
          <div className="flex-1">
            {title && (
              <h5 className="font-semibold mb-1">{title}</h5>
            )}
            <div className="text-sm">{children}</div>
          </div>
        </div>
      </div>
    );
  }
);

Callout.displayName = 'Callout';
