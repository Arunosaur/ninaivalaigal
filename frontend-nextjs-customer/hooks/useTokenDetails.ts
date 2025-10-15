// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC

'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../utils/api-client';
import { TokenStorage } from '../utils/tokenStorage';

type TokenSnapshot = {
  accessToken: string | null;
  refreshToken: string | null;
  accessTokenExpiresAt: number | null;
  refreshTokenExpiresAt: number | null;
};

const emptySnapshot = (): TokenSnapshot => ({
  accessToken: null,
  refreshToken: null,
  accessTokenExpiresAt: null,
  refreshTokenExpiresAt: null,
});

const readTokens = (): TokenSnapshot => {
  if (typeof window === 'undefined') {
    return emptySnapshot();
  }

  return {
    accessToken: TokenStorage.getToken(),
    refreshToken: TokenStorage.getRefreshToken(),
    accessTokenExpiresAt: TokenStorage.getAccessTokenExpiry(),
    refreshTokenExpiresAt: TokenStorage.getRefreshTokenExpiry(),
  };
};

const storageEventKeys = new Set([
  'auth_access_token',
  'auth_access_token_expires',
  'auth_refresh_token',
  'auth_refresh_token_expires',
]);

export function useTokenDetails() {
  const [state, setState] = useState<TokenSnapshot>(() => emptySnapshot());

  const refresh = useCallback(() => {
    setState(readTokens());
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const handleStorage = (event: StorageEvent) => {
      if (!event.key || storageEventKeys.has(event.key)) {
        refresh();
      }
    };

    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
    };
  }, [refresh]);

  useEffect(() => {
    const unsubscribe = apiClient.onRefresh((event) => {
      if (event.status === 'success') {
        refresh();
      }
    });

    return unsubscribe;
  }, [refresh]);

  return {
    ...state,
    refresh,
  };
}
