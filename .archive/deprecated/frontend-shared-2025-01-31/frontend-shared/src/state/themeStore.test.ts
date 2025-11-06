// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach } from 'vitest';
import { useThemeStore } from './themeStore';

describe('ThemeStore', () => {
  beforeEach(() => {
    // Reset store state - default is 'system'
    const state = useThemeStore.getState();
    // Note: store uses persist middleware, may default to 'system'
  });

  it('should initialize with default theme', () => {
    const state = useThemeStore.getState();

    expect(state.theme).toBeDefined();
    expect(['light', 'dark', 'system']).toContain(state.theme);
  });

  it('should set theme', () => {
    const state = useThemeStore.getState();

    state.setTheme('dark');

    const updatedState = useThemeStore.getState();
    expect(updatedState.theme).toBe('dark');
  });

  it('should toggle theme between light and dark', () => {
    const state = useThemeStore.getState();

    state.setTheme('light');
    let updatedState = useThemeStore.getState();
    expect(updatedState.theme).toBe('light');

    state.setTheme('dark');
    updatedState = useThemeStore.getState();
    expect(updatedState.theme).toBe('dark');
  });

  it('should handle system theme', () => {
    const state = useThemeStore.getState();

    state.setTheme('system');

    const updatedState = useThemeStore.getState();
    expect(updatedState.theme).toBe('system');
  });
});
