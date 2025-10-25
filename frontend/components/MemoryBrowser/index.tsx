// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * SPEC-076: Memory Browser Entry Point
 *
 * React integration layer for Memory Browser guided mode.
 * Bridges the existing vanilla JS Memory Browser with React-based guided tour.
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { GuidedTour, type Memory } from './GuidedTour';

/**
 * Memory Browser React Manager
 *
 * Manages React rendering for guided mode within the vanilla JS Memory Browser.
 * Provides bridge between legacy code and modern React components.
 */
export class MemoryBrowserReact {
  private root: Root | null = null;
  private container: HTMLElement | null = null;
  private isGuidedModeActive: boolean = false;

  /**
   * Initialize React integration for Memory Browser
   */
  initialize() {
    // Create container for React components
    this.container = document.createElement('div');
    this.container.id = 'memory-browser-react-root';
    this.container.className = 'fixed inset-0 z-40 pointer-events-none';
    document.body.appendChild(this.container);

    // Create React root
    this.root = createRoot(this.container);

    console.log('✅ Memory Browser React integration initialized');
  }

  /**
   * Start guided tour mode
   * @param memories - Array of memory objects to tour
   * @param onComplete - Callback when tour completes
   * @param onExit - Callback when user exits tour early
   */
  startGuidedTour(
    memories: Memory[],
    onComplete: () => void,
    onExit: () => void
  ) {
    if (!this.root || !this.container) {
      console.error('React not initialized. Call initialize() first.');
      return;
    }

    this.isGuidedModeActive = true;
    this.container.classList.remove('pointer-events-none');
    this.container.classList.add('pointer-events-auto');

    // Render guided tour
    this.root.render(
      <GuidedTour
        memories={memories}
        isActive={true}
        onComplete={() => {
          this.stopGuidedTour();
          onComplete();
        }}
        onExit={() => {
          this.stopGuidedTour();
          onExit();
        }}
      />
    );

    console.log(`🎯 Guided tour started with ${memories.length} memories`);
  }

  /**
   * Stop guided tour mode
   */
  stopGuidedTour() {
    if (!this.root || !this.container) return;

    this.isGuidedModeActive = false;
    this.container.classList.add('pointer-events-none');
    this.container.classList.remove('pointer-events-auto');

    // Clear React tree
    this.root.render(null);

    console.log('🛑 Guided tour stopped');
  }

  /**
   * Check if guided mode is currently active
   */
  isActive(): boolean {
    return this.isGuidedModeActive;
  }

  /**
   * Cleanup React integration
   */
  destroy() {
    if (this.root) {
      this.root.unmount();
      this.root = null;
    }

    if (this.container && this.container.parentElement) {
      this.container.parentElement.removeChild(this.container);
      this.container = null;
    }

    this.isGuidedModeActive = false;

    console.log('🧹 Memory Browser React integration destroyed');
  }
}

// Export singleton instance for global access
export const memoryBrowserReact = new MemoryBrowserReact();

// Auto-initialize on load
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    memoryBrowserReact.initialize();
  });
}

// Make available globally for vanilla JS
if (typeof window !== 'undefined') {
  (window as any).MemoryBrowserReact = memoryBrowserReact;
}

export default memoryBrowserReact;
