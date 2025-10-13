// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/// <reference types="@testing-library/jest-dom" />

import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useSessions } from '../useSessions';

const { getActiveSessions, logoutSession } = vi.hoisted(() => ({
  getActiveSessions: vi.fn(),
  logoutSession: vi.fn(),
}));

vi.mock('../../services/auth.service', () => ({
  authService: {
    getActiveSessions,
    logoutSession,
  },
}));

describe('useSessions', () => {
  beforeEach(() => {
    getActiveSessions.mockReset();
    logoutSession.mockReset();
  });

  it('loads active sessions on mount', async () => {
    const sessions = [
      { id: '1', device: 'MacBook', ip_address: '127.0.0.1', is_current: true, last_active_at: new Date().toISOString() },
    ];

  getActiveSessions.mockResolvedValue({ sessions });

    const { result } = renderHook(() => useSessions());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.sessions).toEqual(sessions);
  expect(getActiveSessions).toHaveBeenCalled();
  });

  it('exposes an error when the fetch fails', async () => {
  getActiveSessions.mockResolvedValue({ error: 'Boom' });

    const { result } = renderHook(() => useSessions());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('Boom');
    expect(result.current.sessions).toEqual([]);
  });

  it('removes a session after logoutSession succeeds', async () => {
    const sessions = [
      { id: '1', device: 'MacBook', ip_address: '127.0.0.1', is_current: false, last_active_at: new Date().toISOString() },
      { id: '2', device: 'iPhone', ip_address: '127.0.0.2', is_current: true, last_active_at: new Date().toISOString() },
    ];

  getActiveSessions.mockResolvedValue({ sessions });
  logoutSession.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useSessions());

    await waitFor(() => expect(result.current.sessions).toHaveLength(2));

    await act(async () => {
      const response = await result.current.logoutSession('1');
      expect(response.success).toBe(true);
    });

    expect(result.current.sessions).toEqual([sessions[1]]);
  });

  it('preserves sessions when logoutSession fails', async () => {
    const sessions = [
      { id: '1', device: 'MacBook', ip_address: '127.0.0.1', is_current: false, last_active_at: new Date().toISOString() },
    ];

  getActiveSessions.mockResolvedValue({ sessions });
  logoutSession.mockResolvedValue({ success: false, error: 'nope' });

    const { result } = renderHook(() => useSessions());

    await waitFor(() => expect(result.current.sessions).toHaveLength(1));

    await act(async () => {
      const response = await result.current.logoutSession('1');
      expect(response.success).toBe(false);
    });

    expect(result.current.sessions).toEqual(sessions);
  });
});
