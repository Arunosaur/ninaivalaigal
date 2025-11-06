// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

import React from 'react';

export interface LoadingSpinnerProps {
  /** Size variant of the spinner */
  size?: 'sm' | 'md' | 'lg';
  /** Optional loading message */
  message?: string;
  /** Additional CSS classes */
  className?: string;
}

export interface FullPageLoadingSpinnerProps {
  /** Optional loading message */
  message?: string;
}

/**
 * LoadingSpinner component for indicating loading states
 *
 * @example
 * ```tsx
 * <LoadingSpinner size="md" message="Loading data..." />
 * ```
 */
export function LoadingSpinner({
  size = 'md',
  message,
  className = ''
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 border-2',
    md: 'w-16 h-16 border-4',
    lg: 'w-24 h-24 border-6',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <div
        className={`${sizeClasses[size]} border-blue-600 border-t-transparent rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="mt-4 text-gray-700 text-center">{message}</p>
      )}
    </div>
  );
}

/**
 * FullPageLoadingSpinner component for full-page loading states
 *
 * @example
 * ```tsx
 * <FullPageLoadingSpinner message="Loading application..." />
 * ```
 */
export function FullPageLoadingSpinner({
  message
}: FullPageLoadingSpinnerProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoadingSpinner size="lg" message={message || 'Loading...'} />
    </div>
  );
}
