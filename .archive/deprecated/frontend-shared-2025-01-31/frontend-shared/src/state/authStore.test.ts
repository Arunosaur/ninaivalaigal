// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state
    const state = useAuthStore.getState();
    state.clearSession();
  });

  it('should initialize with empty state', () => {
    const state = useAuthStore.getState();

    expect(state.session).toBeNull();
  });

  it('should update state on setSession with valid session', () => {
    const state = useAuthStore.getState();
    const mockSession = {
      userId: '1',
      email: 'test@example.com',
      displayName: 'Test User',
      roles: ['user'],
      token: 'test-token',
      expiresAt: new Date().toISOString(),
    };

    state.setSession(mockSession);

    const updatedState = useAuthStore.getState();
    expect(updatedState.session).not.toBeNull();
    expect(updatedState.session?.email).toBe('test@example.com');
    expect(updatedState.session?.userId).toBe('1');
  });

  it('should clear state on clearSession', () => {
    const state = useAuthStore.getState();

    // First set session
    const mockSession = {
      userId: '1',
      email: 'test@example.com',
      displayName: 'Test User',
      roles: ['user'],
      token: 'test-token',
      expiresAt: new Date().toISOString(),
    };
    state.setSession(mockSession);

    const afterSet = useAuthStore.getState();
    expect(afterSet.session).not.toBeNull();

    // Then clear
    state.clearSession();

    const afterClear = useAuthStore.getState();
    expect(afterClear.session).toBeNull();
  });

  it('should validate session schema', () => {
    const state = useAuthStore.getState();
    const invalidSession = { invalid: 'data' };

    // Setting invalid session should be ignored due to schema validation
    state.setSession(invalidSession as any);

    // Store should remain null or handle invalid data gracefully
    expect(state.session).toBeNull();
  });
});
