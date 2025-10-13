// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

'use client';

import { Component, ReactNode } from 'react';
import { Button } from './Button';
import { Card } from './Card';

export interface ErrorBoundaryProps {
  /** Child components to wrap */
  children: ReactNode;
  /** Custom fallback UI to display on error */
  fallback?: ReactNode;
  /** Callback when error occurs */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

/**
 * ErrorBoundary component to catch React errors in child components
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="border-red-300 bg-red-50 p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-red-900">
              ⚠️ Something went wrong
            </h3>
            <p className="text-gray-700">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <Button
              variant="secondary"
              onClick={this.handleReset}
            >
              Try Again
            </Button>
          </div>
        </Card>
      );
    }

    return this.props.children;
  }
}

export interface ErrorMessageProps {
  /** Error title */
  title?: string;
  /** Error message */
  message: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ErrorMessage component for displaying error states
 *
 * @example
 * ```tsx
 * <ErrorMessage
 *   title="Load Failed"
 *   message="Unable to fetch data"
 *   onRetry={handleRetry}
 * />
 * ```
 */
export function ErrorMessage({
  title = 'Error',
  message,
  onRetry,
  className = ''
}: ErrorMessageProps) {
  return (
    <Card className={`border-red-300 bg-red-50 p-6 ${className}`}>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-red-900">⚠️ {title}</h3>
        <p className="text-gray-700">{message}</p>
        {onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Try Again
          </Button>
        )}
      </div>
    </Card>
  );
}
