// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { cva, type VariantProps } from 'class-variance-authority';
import React, { useEffect, useState, useRef, useCallback } from 'react';

import { cn } from '@/utils/cn';

// Overlay variants using class-variance-authority
const overlayVariants = cva(
  // Base styles - applied to all overlays
  [
    'fixed inset-0 z-50',
    'flex items-center justify-center',
    'transition-all duration-300',
  ],
  {
    variants: {
      variant: {
        modal: [
          'bg-black bg-opacity-50',
          'backdrop-blur-sm',
        ],
        spotlight: [
          'bg-black bg-opacity-75',
          'backdrop-blur-sm',
        ],
        guided: [
          'bg-transparent',
          'pointer-events-none',
        ],
        fullscreen: [
          'bg-white',
          'backdrop-blur-none',
        ],
      },
      animation: {
        fade: 'animate-in fade-in duration-300',
        slide: 'animate-in slide-in-from-bottom duration-300',
        zoom: 'animate-in zoom-in-95 duration-300',
        none: '',
      },
    },
    defaultVariants: {
      variant: 'guided',
      animation: 'fade',
    },
  }
);

const contentVariants = cva(
  [
    'relative max-w-2xl mx-auto',
    'bg-white rounded-lg shadow-xl',
    'border border-secondary-200',
    'transition-all duration-300',
  ],
  {
    variants: {
      size: {
        sm: 'max-w-sm p-4',
        md: 'max-w-2xl p-6',
        lg: 'max-w-4xl p-8',
        full: 'max-w-none w-full h-full p-0 rounded-none',
      },
      position: {
        center: 'mx-auto my-auto',
        top: 'mx-auto mt-16',
        bottom: 'mx-auto mb-16',
        'top-left': 'ml-4 mt-4',
        'top-right': 'mr-4 mt-4',
        'bottom-left': 'ml-4 mb-4',
        'bottom-right': 'mr-4 mb-4',
      },
    },
    defaultVariants: {
      size: 'md',
      position: 'center',
    },
  }
);

// Spotlight highlight area
interface SpotlightArea {
  x: number;
  y: number;
  width: number;
  height: number;
  borderRadius?: number;
}

// Overlay component props
export interface OverlayProps extends VariantProps<typeof overlayVariants> {
  isOpen: boolean;
  onClose?: () => void;
  onEscape?: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
  size?: VariantProps<typeof contentVariants>['size'];
  position?: VariantProps<typeof contentVariants>['position'];
  spotlight?: SpotlightArea;
  closeOnBackdrop?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  preventScroll?: boolean;
  focusTrap?: boolean;
}

/**
 * Overlay component for narrative walkthroughs and guided experiences
 *
 * Provides modal, spotlight, and guided overlay modes with accessibility
 * support and integration with SPEC-075 design tokens.
 *
 * @example
 * ```tsx
 * // Modal overlay
 * <Overlay isOpen={showModal} onClose={() => setShowModal(false)} variant="modal">
 *   <h2>Welcome to the guided tour!</h2>
 *   <p>Let's walk through the key features...</p>
 * </Overlay>
 *
 * // Spotlight overlay highlighting specific element
 * <Overlay
 *   isOpen={showSpotlight}
 *   variant="spotlight"
 *   spotlight={{ x: 100, y: 200, width: 300, height: 150 }}
 * >
 *   <div>This highlights the search bar above</div>
 * </Overlay>
 *
 * // Guided overlay for step-by-step walkthrough
 * <Overlay isOpen={showGuide} variant="guided" position="top-right">
 *   <div>Step 1: Click the menu button</div>
 * </Overlay>
 * ```
 */
export const Overlay: React.FC<OverlayProps> = ({
  isOpen,
  onClose,
  onEscape,
  title,
  children,
  variant = 'guided',
  animation = 'fade',
  size = 'md',
  position = 'center',
  className,
  contentClassName,
  spotlight,
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  preventScroll = true,
  focusTrap = true,
  ...props
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && closeOnEscape && isOpen) {
        onEscape?.() || onClose?.();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, closeOnEscape, onEscape, onClose]);

  // Handle body scroll prevention
  useEffect(() => {
    if (isOpen && preventScroll) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen, preventScroll]);

  // Handle focus management
  useEffect(() => {
    if (isOpen && focusTrap) {
      previousFocusRef.current = document.activeElement as HTMLElement;

      // Focus the content container
      setTimeout(() => {
        contentRef.current?.focus();
      }, 100);

      return () => {
        // Return focus to previous element
        previousFocusRef.current?.focus();
      };
    }
  }, [isOpen, focusTrap]);

  // Handle backdrop click
  const handleBackdropClick = useCallback((event: React.MouseEvent) => {
    if (closeOnBackdrop && event.target === overlayRef.current) {
      onClose?.();
    }
  }, [closeOnBackdrop, onClose]);

  // Handle focus trap
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (!focusTrap || !isOpen) return;

    if (event.key === 'Tab') {
      const focusableElements = contentRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements && focusableElements.length > 0) {
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    }
  }, [focusTrap, isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      className={cn(overlayVariants({ variant, animation }), className)}
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'overlay-title' : undefined}
      tabIndex={-1}
      {...props}
    >
      {/* Spotlight Effect */}
      {variant === 'spotlight' && spotlight && (
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ zIndex: -1 }}
        >
          <defs>
            <mask id="spotlight-mask">
              <rect width="100%" height="100%" fill="black" />
              <rect
                x={spotlight.x}
                y={spotlight.y}
                width={spotlight.width}
                height={spotlight.height}
                rx={spotlight.borderRadius || 8}
                fill="white"
              />
            </mask>
          </defs>
          <rect
            width="100%"
            height="100%"
            fill="rgba(0, 0, 0, 0.75)"
            mask="url(#spotlight-mask)"
          />
        </svg>
      )}

      {/* Content Container */}
      <div
        ref={contentRef}
        className={cn(
          contentVariants({ size, position }),
          variant === 'guided' && 'pointer-events-auto',
          contentClassName
        )}
        tabIndex={-1}
        role="document"
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between mb-4">
            {title && (
              <h2
                id="overlay-title"
                className="text-lg font-semibold text-secondary-900"
              >
                {title}
              </h2>
            )}

            {showCloseButton && onClose && (
              <button
                type="button"
                onClick={onClose}
                className={cn(
                  'p-2 rounded-md text-secondary-400',
                  'hover:text-secondary-600 hover:bg-secondary-100',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500'
                )}
                aria-label="Close overlay"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
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
          {children}
        </div>
      </div>
    </div>
  );
};

// Higher-order component for guided tour steps
export interface GuidedStepProps {
  isActive: boolean;
  targetSelector?: string;
  title: string;
  content: React.ReactNode;
  position?: VariantProps<typeof contentVariants>['position'];
  onNext?: () => void;
  onPrevious?: () => void;
  onSkip?: () => void;
  showControls?: boolean;
}

export const GuidedStep: React.FC<GuidedStepProps> = ({
  isActive,
  targetSelector,
  title,
  content,
  position = 'center',
  onNext,
  onPrevious,
  onSkip,
  showControls = true,
}) => {
  const [spotlight, setSpotlight] = useState<SpotlightArea | undefined>();

  // Calculate spotlight area based on target element
  useEffect(() => {
    if (isActive && targetSelector) {
      const targetElement = document.querySelector(targetSelector);
      if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        setSpotlight({
          x: rect.left - 8,
          y: rect.top - 8,
          width: rect.width + 16,
          height: rect.height + 16,
          borderRadius: 8,
        });
      }
    }
  }, [isActive, targetSelector]);

  return (
    <Overlay
      isOpen={isActive}
      variant={targetSelector ? 'spotlight' : 'guided'}
      position={position}
      spotlight={spotlight}
      title={title}
      closeOnBackdrop={false}
      closeOnEscape={false}
      showCloseButton={false}
    >
      <div className="space-y-4">
        <div>{content}</div>

        {showControls && (
          <div className="flex justify-between items-center pt-4 border-t border-secondary-200">
            <button
              type="button"
              onClick={onPrevious}
              className={cn(
                'px-3 py-1 text-sm text-secondary-600',
                'hover:text-secondary-800 focus:outline-none focus:ring-2 focus:ring-primary-500'
              )}
            >
              Previous
            </button>

            <div className="flex space-x-2">
              {onSkip && (
                <button
                  type="button"
                  onClick={onSkip}
                  className={cn(
                    'px-3 py-1 text-sm text-secondary-600',
                    'hover:text-secondary-800 focus:outline-none focus:ring-2 focus:ring-primary-500'
                  )}
                >
                  Skip Tour
                </button>
              )}

              <button
                type="button"
                onClick={onNext}
                className={cn(
                  'px-4 py-2 text-sm font-medium rounded-md',
                  'bg-primary-600 text-white',
                  'hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500'
                )}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </Overlay>
  );
};

export default Overlay;
