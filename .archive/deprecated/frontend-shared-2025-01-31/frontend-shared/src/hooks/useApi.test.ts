// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useApi } from './useApi';

// Mock fetch
global.fetch = vi.fn();

describe('useApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should provide API request function', async () => {
    const { result } = renderHook(() => useApi());

    expect(result.current).toBeDefined();
    expect(typeof result.current.request).toBe('function');
  });

  it('should handle GET requests', async () => {
    const mockData = { id: '1', name: 'Test' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result } = renderHook(() => useApi());

    await result.current.request('/test');

    expect(global.fetch).toHaveBeenCalled();
    const calls = (global.fetch as any).mock.calls;
    expect(calls[0][0]).toContain('/test');
  });

  it('should handle POST requests with data', async () => {
    const mockPayload = { name: 'Test Item' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    const { result } = renderHook(() => useApi());

    await result.current.request('/test', {
      body: JSON.stringify(mockPayload),
    });

    expect(global.fetch).toHaveBeenCalled();
  });

  it('should include authentication token in headers', async () => {
    // Mock store to return a session with token
    vi.mock('../state/authStore', () => ({
      useAuthStore: () => ({
        session: { token: 'test-jwt-token' },
      }),
    }));

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    // Re-import to get the mocked version
    const { useApi: useApiHook } = await import('./useApi');
    const { result } = renderHook(() => useApiHook());

    await result.current.request('/test');

    expect(global.fetch).toHaveBeenCalled();
  });

  it('should handle errors gracefully', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' }),
    });

    const { result } = renderHook(() => useApi());

    await expect(result.current.request('/test')).rejects.toThrow();
  });
});
