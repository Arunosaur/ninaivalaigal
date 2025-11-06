// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

/// <reference types="@testing-library/jest-dom" />

import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useTokenDetails } from '../useTokenDetails';

const refreshListeners: Array<(event: { status: string }) => void> = [];

const tokenFns = vi.hoisted(() => ({
  getToken: vi.fn(),
  getRefreshToken: vi.fn(),
  getAccessTokenExpiry: vi.fn(),
  getRefreshTokenExpiry: vi.fn(),
}));

vi.mock('../../utils/tokenStorage', () => ({
  TokenStorage: {
    getToken: tokenFns.getToken,
    getRefreshToken: tokenFns.getRefreshToken,
    getAccessTokenExpiry: tokenFns.getAccessTokenExpiry,
    getRefreshTokenExpiry: tokenFns.getRefreshTokenExpiry,
  },
}));

vi.mock('../../utils/api-client', () => ({
  apiClient: {
    onRefresh: vi.fn((listener: (event: { status: string }) => void) => {
      refreshListeners.push(listener);
      return () => {
        const index = refreshListeners.indexOf(listener);
        if (index !== -1) {
          refreshListeners.splice(index, 1);
        }
      };
    }),
  },
}));

describe('useTokenDetails', () => {
  beforeEach(() => {
    refreshListeners.length = 0;
    tokenFns.getToken.mockReset();
    tokenFns.getRefreshToken.mockReset();
    tokenFns.getAccessTokenExpiry.mockReset();
    tokenFns.getRefreshTokenExpiry.mockReset();

    tokenFns.getToken.mockReturnValue('access-token');
    tokenFns.getRefreshToken.mockReturnValue('refresh-token');
    tokenFns.getAccessTokenExpiry.mockReturnValue(1_700_000_000);
    tokenFns.getRefreshTokenExpiry.mockReturnValue(1_700_000_100);
  });

  it('reads token information from storage on mount', () => {
    const { result } = renderHook(() => useTokenDetails());

    return waitFor(() => {
      expect(result.current.accessToken).toBe('access-token');
      expect(result.current.refreshToken).toBe('refresh-token');
      expect(result.current.accessTokenExpiresAt).toBe(1_700_000_000);
      expect(result.current.refreshTokenExpiresAt).toBe(1_700_000_100);
    });
  });

  it('refreshes token information when requested', () => {
    const { result } = renderHook(() => useTokenDetails());

    tokenFns.getToken.mockReturnValue('next-access');
    tokenFns.getRefreshToken.mockReturnValue('next-refresh');
    tokenFns.getAccessTokenExpiry.mockReturnValue(1_800_000_000);
    tokenFns.getRefreshTokenExpiry.mockReturnValue(1_800_000_100);

    act(() => {
      result.current.refresh();
    });

    return waitFor(() => {
      expect(result.current.accessToken).toBe('next-access');
      expect(result.current.refreshToken).toBe('next-refresh');
      expect(result.current.accessTokenExpiresAt).toBe(1_800_000_000);
      expect(result.current.refreshTokenExpiresAt).toBe(1_800_000_100);
    });
  });

  it('updates when the API client signals a refresh success', async () => {
    const { result } = renderHook(() => useTokenDetails());

    tokenFns.getToken.mockReturnValue('refreshed-access');
    tokenFns.getRefreshToken.mockReturnValue('refreshed-refresh');

    act(() => {
      refreshListeners.forEach((listener) => listener({ status: 'success' }));
    });

    await waitFor(() => {
      expect(result.current.accessToken).toBe('refreshed-access');
      expect(result.current.refreshToken).toBe('refreshed-refresh');
    });
  });

  it('responds to storage events for token keys', async () => {
    const { result } = renderHook(() => useTokenDetails());

    tokenFns.getToken.mockReturnValue('storage-access');
    tokenFns.getAccessTokenExpiry.mockReturnValue(1_900_000_000);

    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'auth_access_token' }));
    });

    await waitFor(() => {
      expect(result.current.accessToken).toBe('storage-access');
      expect(result.current.accessTokenExpiresAt).toBe(1_900_000_000);
    });
  });
});
