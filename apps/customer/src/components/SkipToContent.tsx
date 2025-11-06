// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * Skip to Content Link Component
 *
 * WCAG AA Accessibility: Provides keyboard users with a way to skip navigation
 * and jump directly to the main content. This is critical for screen reader users
 * and keyboard-only navigation.
 *
 * Usage: Add this component at the top of your page layout, typically right after
 * the opening <body> or main container.
 *
 * @example
 * ```tsx
 * <div>
 *   <SkipToContent />
 *   <Navigation />
 *   <main id="main-content">
 *     {/* Page content */}
 *   </main>
 * </div>
 * ```
 */

import { useEffect, useRef } from 'react';

interface SkipToContentProps {
  /**
   * The ID of the main content element to skip to.
   * Default: 'main-content'
   */
  targetId?: string;
  /**
   * The text to display in the skip link.
   * Default: 'Skip to main content'
   */
  label?: string;
  /**
   * Additional CSS classes to apply.
   */
  className?: string;
}

export function SkipToContent({
  targetId = 'main-content',
  label = 'Skip to main content',
  className = '',
}: SkipToContentProps) {
  const linkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    // Focus the link when it becomes visible (e.g., on Tab key press)
    const handleFocus = () => {
      linkRef.current?.focus();
    };

    // Add keyboard event listener for Tab key
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab' && !event.shiftKey && linkRef.current) {
        // Focus the skip link when Tab is first pressed
        linkRef.current.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Set tabindex so the element can receive focus
      target.setAttribute('tabindex', '-1');
      target.focus();
    }
  };

  return (
    <a
      ref={linkRef}
      href={`#${targetId}`}
      onClick={handleClick}
      className={`
        sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100]
        focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-lg
        focus:shadow-lg focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
        focus:outline-none focus:font-semibold
        ${className}
      `}
      aria-label={label}
    >
      {label}
    </a>
  );
}
