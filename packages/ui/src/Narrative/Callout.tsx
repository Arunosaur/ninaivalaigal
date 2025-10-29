// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { cva, type VariantProps } from 'class-variance-authority';
import React, { useState, useRef, useEffect } from 'react';

import { cn } from '../utils/cn';

// Callout variants using class-variance-authority
const calloutVariants = cva(
  // Base styles - applied to all callouts
  [
    'relative inline-block max-w-xs',
    'bg-slate-800 border rounded-lg shadow-lg',
    'text-sm leading-relaxed',
    'transition-all duration-200',
    'z-50',
  ],
  {
    variants: {
      variant: {
        tooltip: [
          'p-3 border-slate-700 text-slate-200',
          'shadow-md',
        ],
        annotation: [
          'p-4 border-indigo-700',
          'shadow-lg ring-1 ring-indigo-500/30',
          'bg-gradient-to-br from-indigo-900/50 to-slate-800 text-slate-200',
        ],
        warning: [
          'p-3 border-warning-300',
          'bg-warning-50 text-warning-800',
          'shadow-md',
        ],
        error: [
          'p-3 border-error-300',
          'bg-error-50 text-error-800',
          'shadow-md',
        ],
        success: [
          'p-3 border-success-300',
          'bg-success-50 text-success-800',
          'shadow-md',
        ],
        ai: [
          'p-4 border-indigo-700',
          'bg-gradient-to-br from-indigo-900/50 to-slate-800',
          'shadow-lg ring-2 ring-indigo-500/30',
          'text-slate-200',
        ],
      },
      size: {
        sm: 'max-w-xs text-xs p-2',
        md: 'max-w-sm text-sm p-3',
        lg: 'max-w-md text-base p-4',
        xl: 'max-w-lg text-base p-5',
      },
      position: {
        top: 'mb-2',
        bottom: 'mt-2',
        left: 'mr-2',
        right: 'ml-2',
        'top-left': 'mb-2 mr-2',
        'top-right': 'mb-2 ml-2',
        'bottom-left': 'mt-2 mr-2',
        'bottom-right': 'mt-2 ml-2',
      },
    },
    defaultVariants: {
      variant: 'tooltip',
      size: 'md',
      position: 'top',
    },
  }
);

// Arrow/pointer variants
const arrowVariants = cva(
  [
    'absolute w-3 h-3 transform rotate-45',
    'border border-slate-700 bg-slate-800',
  ],
  {
    variants: {
      variant: {
        tooltip: 'border-slate-700 bg-slate-800',
        annotation: 'border-indigo-700 bg-indigo-900/50',
        warning: 'border-warning-300 bg-warning-50',
        error: 'border-error-300 bg-error-50',
        success: 'border-success-300 bg-success-50',
        ai: 'border-indigo-700 bg-indigo-900/50',
      },
      position: {
        top: '-bottom-1.5 left-1/2 -translate-x-1/2 border-t-0 border-l-0',
        bottom: '-top-1.5 left-1/2 -translate-x-1/2 border-b-0 border-r-0',
        left: '-right-1.5 top-1/2 -translate-y-1/2 border-l-0 border-b-0',
        right: '-left-1.5 top-1/2 -translate-y-1/2 border-r-0 border-t-0',
        'top-left': '-bottom-1.5 left-4 border-t-0 border-l-0',
        'top-right': '-bottom-1.5 right-4 border-t-0 border-l-0',
        'bottom-left': '-top-1.5 left-4 border-b-0 border-r-0',
        'bottom-right': '-top-1.5 right-4 border-b-0 border-r-0',
      },
    },
    defaultVariants: {
      variant: 'tooltip',
      position: 'top',
    },
  }
);

// AI context metadata interface
export interface AIContext {
  confidence: number;
  source: string;
  relatedMemories?: string[];
  tags?: string[];
  timestamp?: Date;
  reasoning?: string;
}

// Callout component props
export interface CalloutProps extends VariantProps<typeof calloutVariants> {
  content: React.ReactNode;
  title?: string;
  isVisible?: boolean;
  onClose?: () => void;
  onInteraction?: (action: string) => void;
  className?: string;
  showArrow?: boolean;
  aiContext?: AIContext;
  interactive?: boolean;
  autoHide?: number; // Auto-hide after N milliseconds
  children?: React.ReactNode;
}

// AI confidence indicator
const ConfidenceIndicator: React.FC<{ confidence: number }> = ({ confidence }) => {
  const getColor = (conf: number) => {
    if (conf >= 0.8) return 'text-success-600';
    if (conf >= 0.6) return 'text-warning-600';
    return 'text-error-600';
  };

  const getLabel = (conf: number) => {
    if (conf >= 0.8) return 'High confidence';
    if (conf >= 0.6) return 'Medium confidence';
    return 'Low confidence';
  };

  return (
    <div className="flex items-center space-x-1 text-xs">
      <div className={cn('w-2 h-2 rounded-full', getColor(confidence).replace('text-', 'bg-'))} />
      <span className={getColor(confidence)}>
        {getLabel(confidence)} ({Math.round(confidence * 100)}%)
      </span>
    </div>
  );
};

/**
 * Callout component for AI-generated annotations and contextual information
 *
 * Provides tooltips, annotations, and AI-powered contextual callouts with
 * confidence indicators and interactive features.
 *
 * @example
 * ```tsx
 * // Basic tooltip
 * <Callout content="This is a helpful tooltip" variant="tooltip">
 *   <button>Hover me</button>
 * </Callout>
 *
 * // AI-powered annotation
 * <Callout
 *   variant="ai"
 *   title="AI Insight"
 *   content="This memory relates to your project planning from last week"
 *   aiContext={{
 *     confidence: 0.85,
 *     source: "SPEC-040 Feedback Loop",
 *     relatedMemories: ["mem_123", "mem_456"],
 *     tags: ["planning", "project"]
 *   }}
 *   interactive
 * />
 *
 * // Warning callout
 * <Callout
 *   variant="warning"
 *   content="This action cannot be undone"
 *   position="bottom"
 * />
 * ```
 */
export const Callout: React.FC<CalloutProps> = ({
  content,
  title,
  isVisible = true,
  onClose,
  onInteraction,
  variant = 'tooltip',
  size = 'md',
  position = 'top',
  className,
  showArrow = true,
  aiContext,
  interactive = false,
  autoHide,
  children,
  ...props
}) => {
  const [visible, setVisible] = useState(isVisible);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const calloutRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  // Handle auto-hide (pause on hover OR focus for keyboard accessibility)
  useEffect(() => {
    if (autoHide && visible && !isHovered && !isFocused) {
      timeoutRef.current = setTimeout(() => {
        setVisible(false);
        onClose?.();
      }, autoHide);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [autoHide, visible, isHovered, isFocused, onClose]);

  // Handle visibility changes
  useEffect(() => {
    setVisible(isVisible);
  }, [isVisible]);

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  const handleInteraction = (action: string) => {
    onInteraction?.(action);
  };

  if (!visible) return children || null;

  const calloutElement = (
    <div
      ref={calloutRef}
      className={cn(calloutVariants({ variant, size, position }), className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      role={interactive ? 'dialog' : 'tooltip'}
      aria-live="polite"
      {...props}
    >
      {/* Arrow */}
      {showArrow && (
        <div className={arrowVariants({ variant, position })} />
      )}

      {/* Header */}
      {(title || onClose || aiContext) && (
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            {title && (
              <h4 className="font-medium text-secondary-900 mb-1">
                {title}
              </h4>
            )}

            {aiContext && (
              <ConfidenceIndicator confidence={aiContext.confidence} />
            )}
          </div>

          {onClose && (
            <button
              type="button"
              onClick={handleClose}
              className={cn(
                'ml-2 p-1 rounded text-secondary-400',
                'hover:text-secondary-600 hover:bg-secondary-100',
                'focus:outline-none focus:ring-1 focus:ring-primary-500'
              )}
              aria-label="Close callout"
            >
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          )}
        </div>
      )}

      {/* Content */}
      <div className="text-secondary-700">
        {content}
      </div>

      {/* AI Context Details */}
      {aiContext && (
        <div className="mt-3 pt-3 border-t border-secondary-200 space-y-2">
          {aiContext.source && (
            <div className="text-xs text-secondary-600">
              <span className="font-medium">Source:</span> {aiContext.source}
            </div>
          )}

          {aiContext.tags && aiContext.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {aiContext.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-primary-100 text-primary-800"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {aiContext.relatedMemories && aiContext.relatedMemories.length > 0 && (
            <div className="text-xs text-secondary-600">
              <span className="font-medium">Related:</span> {aiContext.relatedMemories.length} memories
            </div>
          )}
        </div>
      )}

      {/* Interactive Actions */}
      {interactive && (
        <div className="mt-3 pt-3 border-t border-secondary-200 flex space-x-2">
          <button
            type="button"
            onClick={() => handleInteraction('helpful')}
            className={cn(
              'px-2 py-1 text-xs rounded',
              'bg-success-100 text-success-700 hover:bg-success-200',
              'focus:outline-none focus:ring-1 focus:ring-success-500'
            )}
          >
            👍 Helpful
          </button>

          <button
            type="button"
            onClick={() => handleInteraction('not-helpful')}
            className={cn(
              'px-2 py-1 text-xs rounded',
              'bg-secondary-100 text-secondary-700 hover:bg-secondary-200',
              'focus:outline-none focus:ring-1 focus:ring-secondary-500'
            )}
          >
            👎 Not helpful
          </button>

          {aiContext?.relatedMemories && (
            <button
              type="button"
              onClick={() => handleInteraction('explore')}
              className={cn(
                'px-2 py-1 text-xs rounded',
                'bg-primary-100 text-primary-700 hover:bg-primary-200',
                'focus:outline-none focus:ring-1 focus:ring-primary-500'
              )}
            >
              🔍 Explore
            </button>
          )}
        </div>
      )}
    </div>
  );

  // If children are provided, render as a positioned callout
  if (children) {
    return (
      <div
        className="relative inline-block"
        aria-haspopup={interactive ? 'dialog' : undefined}
        aria-expanded={interactive ? visible : undefined}
      >
        {children}
        {visible && calloutElement}
      </div>
    );
  }

  // Otherwise render as standalone callout
  return calloutElement;
};

// Hook for managing multiple callouts
export const useCallouts = () => {
  const [callouts, setCallouts] = useState<Array<{
    id: string;
    props: CalloutProps;
  }>>([]);

  const showCallout = (id: string, props: CalloutProps) => {
    setCallouts(prev => [
      ...prev.filter(c => c.id !== id),
      { id, props }
    ]);
  };

  const hideCallout = (id: string) => {
    setCallouts(prev => prev.filter(c => c.id !== id));
  };

  const hideAllCallouts = () => {
    setCallouts([]);
  };

  return {
    callouts,
    showCallout,
    hideCallout,
    hideAllCallouts,
  };
};

export default Callout;
