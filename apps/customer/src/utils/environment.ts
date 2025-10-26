// SPDX-License-Identifier: Proprietary
// Environment detection helpers shared between browser and test contexts.

export const isBrowser = typeof window !== 'undefined';

export const prefersReducedMotion = () =>
  isBrowser && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
