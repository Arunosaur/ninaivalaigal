// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAuth } from './useAuth';
import { useAuthStore } from '../state/authStore';
import { fetchApi } from '../lib/api';

// Mock the modules
vi.mock('../state/authStore');
vi.mock('../lib/api');

describe('useAuth', () => {
  const mockSetSession = vi.fn();
  const mockClearSession = vi.fn();
  const mockFetchApi = vi.mocked(fetchApi);

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useAuthStore).mockReturnValue({
      session: null,
      setSession: mockSetSession,
      clearSession: mockClearSession,
    } as any);
  });

  it('should return authentication state', () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current).toBeDefined();
    expect(result.current).toHaveProperty('session');
    expect(result.current).toHaveProperty('isAuthenticated');
    expect(result.current).toHaveProperty('login');
    expect(result.current).toHaveProperty('logout');
  });

  it('should provide login function', () => {
    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.login).toBe('function');
  });

  it('should provide logout function', () => {
    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.logout).toBe('function');
  });

  it('should handle authentication state correctly when session is null', () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.session).toBeNull();
  });

  it('should call login with correct credentials', async () => {
    const mockSession = {
      userId: '1',
      email: 'test@example.com',
      displayName: 'Test User',
      roles: ['user'],
      token: 'test-token',
      expiresAt: new Date().toISOString(),
    };

    mockFetchApi.mockResolvedValueOnce({ session: mockSession });

    const { result } = renderHook(() => useAuth());

    const session = await result.current.login('test@example.com', 'password123');

    expect(mockFetchApi).toHaveBeenCalledWith('/auth/login', expect.objectContaining({
      baseUrl: '/api',
      headers: expect.objectContaining({
        Authorization: expect.stringContaining('Basic'),
      }),
    }));
    expect(mockSetSession).toHaveBeenCalledWith(mockSession);
    expect(session).toEqual(mockSession);
  });

  it('should encode credentials in Basic auth header', async () => {
    mockFetchApi.mockResolvedValueOnce({ session: {} as any });

    const { result } = renderHook(() => useAuth());

    await result.current.login('test@example.com', 'password123');

    const callArgs = mockFetchApi.mock.calls[0];
    const authHeader = callArgs[1]?.headers?.Authorization;
    expect(authHeader).toContain('Basic');
    // Decode and verify
    const encoded = authHeader.replace('Basic ', '');
    const decoded = atob(encoded);
    expect(decoded).toBe('test@example.com:password123');
  });

  it('should handle login errors', async () => {
    const error = new Error('Invalid credentials');
    mockFetchApi.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useAuth());

    await expect(result.current.login('test@example.com', 'wrong')).rejects.toThrow('Invalid credentials');
    expect(mockSetSession).not.toHaveBeenCalled();
  });

  it('should call logout and clear session', async () => {
    mockFetchApi.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useAuth());

    await result.current.logout();

    expect(mockFetchApi).toHaveBeenCalledWith('/auth/logout');
    expect(mockClearSession).toHaveBeenCalled();
  });

  it('should propagate logout errors', async () => {
    mockFetchApi.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useAuth());

    // Logout doesn't have error handling - error propagates
    await expect(result.current.logout()).rejects.toThrow('Network error');

    // API is called, but clearSession is not called because error occurs first
    expect(mockFetchApi).toHaveBeenCalledWith('/auth/logout');
    expect(mockClearSession).not.toHaveBeenCalled();
  });
});
